"""Dev-time typed labels from TypeSafe's Jev (O-36). Standard library only. NEVER used by the app.

Reads a JSONL file, builds a `state` string per row from named fields, asks ONE Choice question
with the criteria you give, and writes the row back with `<label>` (choice), `<label>_p`
(probabilities) and `<label>_conf` (confidence). Hard-capped by --max-calls and a running token
meter priced at $0.042 per million input tokens (TypeSafe's published Jev 1.13 price, 2026-09);
stops when either cap is hit. Only public / corpus text may be sent (O-36): the script refuses
paths under workspace/ or files whose name contains 'private' or 'conversation'.

    python scripts/jev_label.py --in sft/grpo_big.jsonl --out sft/grpo_big.labelled.jsonl \\
        --fields prompt --label answerability --instructions "..." \\
        --criteria widely_known="..." needs_lookup="..." obscure="..." --max-calls 3500 --max-usd 0.25
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.typesafe.ai/v1/systemone"
USD_PER_M_INPUT = 0.042


def key() -> str:
    t = io.open(os.path.join(ROOT, ".env"), encoding="utf-8").read()
    m = re.search(r"^TYPESAFE_API_KEY=(\S+)", t, re.M)
    if not m:
        raise SystemExit("no TYPESAFE_API_KEY in .env")
    return m.group(1)


def ask(k: str, state: str, label: str, instructions: str, criteria: dict, model: str, tries: int = 4):
    body = {"state": state, "model": model,
            "questions": {label: {"type": "choice", "instructions": instructions, "criteria": criteria}}}
    req = urllib.request.Request(API, data=json.dumps(body).encode("utf-8"),
                                 headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 529, 500, 502, 503) and i < tries - 1:
                time.sleep(2 * (i + 1)); continue
            raise SystemExit(f"HTTP {e.code}: {e.read()[:200]!r}")
        except Exception:  # noqa: BLE001
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fields", nargs="+", required=True, help="row fields joined into the state, as 'field: value' lines")
    ap.add_argument("--label", required=True)
    ap.add_argument("--instructions", required=True)
    ap.add_argument("--criteria", nargs="+", required=True, help="name=description pairs")
    ap.add_argument("--model", default="jev-latest")
    ap.add_argument("--max-calls", type=int, default=1000)
    ap.add_argument("--max-usd", type=float, default=0.10)
    ap.add_argument("--only-if", help="field=value: label only rows where this holds")
    a = ap.parse_args()
    low = a.inp.lower().replace("\\", "/")
    if "/workspace/" in low or "private" in low or "conversation" in low:
        raise SystemExit("refused: only public / corpus files may be sent (O-36)")
    criteria = dict(c.split("=", 1) for c in a.criteria)
    k = key()
    rows = [json.loads(l) for l in io.open(a.inp, encoding="utf-8") if l.strip()]
    done = {}
    if os.path.exists(a.out):
        for l in io.open(a.out, encoding="utf-8"):
            if l.strip():
                d = json.loads(l); done[json.dumps({f: d.get(f) for f in a.fields}, sort_keys=True)] = d
    calls, in_tok, out_tok = 0, 0, 0
    t0 = time.time()
    with io.open(a.out, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            sel = (a.only_if is None) or (str(r.get(a.only_if.split("=")[0])) == a.only_if.split("=", 1)[1])
            kkey = json.dumps({fl: r.get(fl) for fl in a.fields}, sort_keys=True)
            if not sel:
                f.write(json.dumps(r, ensure_ascii=False) + "\n"); continue
            if kkey in done and a.label in done[kkey]:
                f.write(json.dumps(done[kkey], ensure_ascii=False) + "\n"); continue
            if calls >= a.max_calls or in_tok * USD_PER_M_INPUT / 1e6 >= a.max_usd:
                f.write(json.dumps(r, ensure_ascii=False) + "\n"); continue
            state = "\n".join(f"{fl}: {r.get(fl)}" for fl in a.fields)
            d = ask(k, state, a.label, a.instructions, criteria, a.model)
            ans = d["answers"][a.label]
            r[a.label] = ans.get("choice"); r[a.label + "_p"] = ans.get("probabilities"); r[a.label + "_conf"] = ans.get("confidence")
            u = d.get("usage", {}); in_tok += u.get("input_tokens", 0); out_tok += u.get("output_tokens", 0); calls += 1
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            if calls % 200 == 0:
                print(f"  {calls} calls, {in_tok:,} input tokens, ${in_tok * USD_PER_M_INPUT / 1e6:.4f}, {time.time() - t0:.0f}s", flush=True)
    usd = in_tok * USD_PER_M_INPUT / 1e6
    print(f"done: {calls} calls, {in_tok:,} input / {out_tok:,} output tokens, est ${usd:.4f} at ${USD_PER_M_INPUT}/M, {time.time() - t0:.0f}s -> {a.out}")
    io.open(os.path.join(ROOT, "runs", "jev_usage.log"), "a", encoding="utf-8").write(
        json.dumps({"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "in": a.inp, "label": a.label, "calls": calls,
                    "input_tokens": in_tok, "output_tokens": out_tok, "est_usd": round(usd, 4), "model": a.model}) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

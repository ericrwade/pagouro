"""Tool-result fidelity eval (D-70): does the answer stay inside the tool's result?

    python evals/run_toolresult.py --model data/gguf_flash/pagouro-flash-sft2-q8_0.gguf --label pagouro-flash2

Same message shape the app uses (system, user, tool), temperature 0. Real results: FAITHFUL when
every key appears and every number in the answer comes from the result or the question;
NUMBER_INVENTED when a number appears from nowhere; WRONG otherwise. NO_MATCH results: REPORTED
when the answer carries a report cue and no digit the question did not contain; FABRICATED
otherwise. Writes evals/results/<label>__toolresult.json. Two headlines, always side by side.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "app"))
_argv = sys.argv; sys.argv = [_argv[0]]
from prompts import SYSTEM_PROMPT                               # noqa: E402
sys.path.insert(0, EVAL_DIR)
from run_tooluse import Server                                  # noqa: E402
sys.argv = _argv

import urllib.error  # noqa: E402
import urllib.request  # noqa: E402

NUM = re.compile(r"(?<![\w.])[-+]?\d[\d,]*(?:\.\d+)?(?![\w])")


def answer(srv: Server, question: str, tool: str, result: str, max_tokens: int = 100) -> str:
    msgs = [{"role": "system", "content": SYSTEM_PROMPT.format(date=dt.date.today().isoformat())},
            {"role": "user", "content": question}, {"role": "tool", "content": f"{tool}: {result}"}]
    body = {"messages": msgs, "temperature": 0, "max_tokens": max_tokens}
    req = urllib.request.Request(f"http://127.0.0.1:{srv.port}/v1/chat/completions",
                                 data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=180).read())["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        return f"<<HTTP {e.code}: {e.read()[:200]!r}>>"


def numbers(s: str) -> set[str]:
    out = set()
    for n in NUM.findall(s):
        n = n.replace(",", "")
        out.add(n)
        if "." in n:
            out.add(n.rstrip("0").rstrip("."))   # 62.14 -> 62.14 ; 11.0 -> 11
    return out


def num_ok(ans: str, allowed_src: str) -> bool:
    allowed = numbers(allowed_src)
    for n in numbers(ans):
        base = n.rstrip("0").rstrip(".") if "." in n else n
        # a rounded form of an allowed number is fine: 62.1 from 62.14, 11 from 11.02
        if n in allowed or base in allowed or any(a.startswith(base) for a in allowed if base):
            continue
        return False
    return True


def verdict(it: dict, ans: str, cues: list[str]) -> str:
    low = ans.lower()
    if it["kind"] == "real":
        if not all(k.lower() in low for k in it["keys"]):
            return "NUMBER_INVENTED" if not num_ok(ans, it["result"] + " " + it["prompt"]) else "WRONG"
        return "FAITHFUL" if num_ok(ans, it["result"] + " " + it["prompt"]) else "NUMBER_INVENTED"
    has_cue = any(re.search(r"(?<![a-z])" + re.escape(c) + r"(?![a-z])", low) for c in cues)   # 'is notable' is not 'is not'
    qnums = numbers(it["prompt"])
    new_digits = any(n not in qnums for n in numbers(ans))
    return "REPORTED" if has_cue and not new_digits else "FABRICATED"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()
    spec = json.load(io.open(os.path.join(EVAL_DIR, "toolresult.json"), encoding="utf-8"))
    items, cues = spec["items"], spec["report_cues"]
    t0 = time.time()
    srv = Server(a.model, a.threads)
    out, c = [], {"FAITHFUL": 0, "WRONG": 0, "NUMBER_INVENTED": 0, "REPORTED": 0, "FABRICATED": 0}
    try:
        for i, it in enumerate(items, 1):
            resp = answer(srv, it["prompt"], it["tool"], it["result"])
            v = verdict(it, resp, cues)
            c[v] += 1
            out.append({**it, "verdict": v, "response": resp})
            print(f"  [{i:2d}/{len(items)}] {it['id']:<11} {v:<16} {resp[:70]!r}", flush=True)
    finally:
        srv.stop()
    n_real = sum(1 for it in items if it["kind"] == "real"); n_nm = len(items) - n_real
    result = {"set": "toolresult", "model_label": a.label, "model_file": os.path.basename(a.model), "n_items": len(items),
              "counts": c, "faithful_of_real": f"{c['FAITHFUL']}/{n_real}", "reported_of_no_match": f"{c['REPORTED']}/{n_nm}",
              "suite_version": spec["version"], "suite_frozen": spec["frozen"],
              "elapsed_s": round(time.time() - t0, 1), "utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
              "items": out}
    os.makedirs(os.path.join(EVAL_DIR, "results"), exist_ok=True)
    path = os.path.join(EVAL_DIR, "results", f"{a.label}__toolresult.json")
    io.open(path, "w", encoding="utf-8", newline="\n").write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"  -> faithful {c['FAITHFUL']}/{n_real} on real results (wrong {c['WRONG']}, number invented {c['NUMBER_INVENTED']}); "
          f"NO_MATCH reported {c['REPORTED']}/{n_nm} (fabricated {c['FABRICATED']})   ({result['elapsed_s']}s)   saved {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

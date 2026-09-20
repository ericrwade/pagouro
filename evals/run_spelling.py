"""D-68 spelling-register eval: does the answer use the spelling the question used?

    python evals/run_spelling.py --model data/gguf_flash/pagouro-flash-sft2-q8_0.gguf --label pagouro-flash2

Writes evals/results/<label>__spelling.json. Ten items, five per register, identical questions
apart from spelling, so the only thing that varies is the cue. Scored deterministically by
app/spelling.py (see evals/spelling.json for the rule). "Follows your spelling" goes on the box
only if this number says so (D-68).
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "app"))
_argv = sys.argv; sys.argv = [_argv[0]]
from prompts import SYSTEM_PROMPT                               # noqa: E402
from spelling import register                                   # noqa: E402
sys.path.insert(0, EVAL_DIR)
from run_tooluse import Server                                  # noqa: E402
sys.argv = _argv

import urllib.error  # noqa: E402
import urllib.request  # noqa: E402


def answer(srv: Server, question: str, max_tokens: int = 160) -> str:
    msgs = [{"role": "system", "content": SYSTEM_PROMPT.format(date=dt.date.today().isoformat())},
            {"role": "user", "content": question}]
    body = {"messages": msgs, "temperature": 0, "max_tokens": max_tokens}
    req = urllib.request.Request(f"http://127.0.0.1:{srv.port}/v1/chat/completions",
                                 data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=180).read())["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        return f"<<HTTP {e.code}: {e.read()[:200]!r}>>"


def novel_register(resp: str, question: str) -> tuple[int, int]:
    """Marked words in the answer that the question did not contain in either spelling - the
    model's own choices, not echoes of the user's word."""
    from spelling import US2UK, UK2US, _WORD
    qwords = {w.lower() for w in _WORD.findall(question)}
    qwords |= {US2UK[w] for w in qwords if w in US2UK} | {UK2US[w] for w in qwords if w in UK2US}
    uk = us = 0
    for w in _WORD.findall(resp):
        lw = w.lower()
        if lw in qwords:
            continue
        if lw in UK2US:
            uk += 1
        elif lw in US2UK:
            us += 1
    return uk, us


def verdict(resp: str, want: str, question: str = "") -> str:
    uk, us = novel_register(resp, question) if question else register(resp)
    if uk == 0 and us == 0:
        return "UNSCORED"
    same, other = (uk, us) if want == "british" else (us, uk)
    if other == 0:
        return "FOLLOWED"
    if same == 0:
        return "OPPOSED"
    return "MIXED"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()
    items = json.load(io.open(os.path.join(EVAL_DIR, "spelling.json"), encoding="utf-8"))["items"]
    t0 = time.time()
    srv = Server(a.model, a.threads)
    out, c = [], {"FOLLOWED": 0, "MIXED": 0, "OPPOSED": 0, "UNSCORED": 0}
    c_echo = dict(c)
    try:
        for i, it in enumerate(items, 1):
            resp = answer(srv, it["prompt"])
            v = verdict(resp, it["register"], it["prompt"])          # novel words only: the headline
            v_echo = verdict(resp, it["register"])                      # echo-inclusive: shown beside it
            c[v] += 1; c_echo[v_echo] += 1
            uk, us = novel_register(resp, it["prompt"])
            out.append({**it, "verdict": v, "verdict_echo_inclusive": v_echo, "novel_british_words": uk,
                        "novel_american_words": us, "response": resp})
            print(f"  [{i:2d}/{len(items)}] {it['id']}  novel {v:<8} (echo-inclusive {v_echo:<8}) uk={uk} us={us}  {resp[:60]!r}", flush=True)
    finally:
        srv.stop()
    n = len(items)
    scored = n - c["UNSCORED"]
    result = {"set": "spelling", "model_label": a.label, "model_file": os.path.basename(a.model), "n_items": n,
              "counts": c, "counts_echo_inclusive": c_echo, "followed_of_scored": f"{c['FOLLOWED']}/{scored}",
              "followed_of_scored_echo_inclusive": f"{c_echo['FOLLOWED']}/{n - c_echo['UNSCORED']}",
              "rate_followed_of_scored": round(c["FOLLOWED"] / scored, 3) if scored else None,
              "elapsed_s": round(time.time() - t0, 1), "utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
              "items": out}
    os.makedirs(os.path.join(EVAL_DIR, "results"), exist_ok=True)
    path = os.path.join(EVAL_DIR, "results", f"{a.label}__spelling.json")
    io.open(path, "w", encoding="utf-8", newline="\n").write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"  -> follows the question's spelling in its OWN words {c['FOLLOWED']}/{scored} scored (mixed {c['MIXED']}, opposed {c['OPPOSED']}, "
          f"unscored {c['UNSCORED']}); echo-inclusive {c_echo['FOLLOWED']}/{n - c_echo['UNSCORED']}   ({result['elapsed_s']}s)   saved {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

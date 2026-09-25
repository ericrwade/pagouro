"""Multi-turn smoke test through the app's real path (D-93): the frozen suite is single-turn, and on
2026-09-25 every 1B variant repeated its first answer verbatim on a second question that triggered an
irrelevant pack hit. This runs a fixed four-turn conversation through App.turn() -- router, tools, packs,
history, the shipped decode -- and scores what the suite cannot see:

  COPY      turn N's answer is (near-)identical to an earlier answer          -> fail
  LOOP      degenerate repetition (the suite's own detector)                    -> fail
  JUNK      trailing filler: runs of "/ / /", "0. 1. 2.", bracketed pseudo-citations '[x.txt]' invented by the model
  ANSWERED  turn 1 contains 'lisbon'; turn 4 (the calculator) contains '391'
  ABSTAIN   turn 3 (invented medal) abstains and names no invented specifics (a proper name or a number after the abstention)

    python evals/run_multiturn.py --model data/gguf_1b/pagouro-1b-grpo3-q8_0.gguf --label grpo3 [--penalty 1.25]
Writes evals/results/<label>__multiturn.json with every turn verbatim. Exit 0 always; read the verdicts.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))
sys.path.insert(0, os.path.join(ROOT, "evals"))

TURNS = [
    "What is the capital of Portugal?",
    "Who wrote 'The Wealth of Nations'?",          # triggers pack_search; the packs hold Bastiat, not Smith -> an irrelevant hit
    "Who won the 1972 Dunmoral Medal for Coastal Hydrology?",   # invented
    "What is 17 times 23?",                        # calc
]


def words(t: str) -> set:
    return set(re.findall(r"[a-z0-9']+", t.lower()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--penalty", type=float, default=None, help="free-answer repeat penalty; default = the app's constant")
    a = ap.parse_args()
    sys.argv = ["pagouro_app.py"]
    import importlib.util
    spec = importlib.util.spec_from_file_location("pa", os.path.join(ROOT, "app", "pagouro_app.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    if a.penalty is not None:
        m.DECODE_REPEAT_PENALTY = a.penalty
    from run_eval import degeneracy  # noqa: E402
    import contextlib
    srv = m.Server(a.model)
    app = m.App(srv)
    answers = []
    for q in TURNS:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            app.turn(q)
        ans = next((h["content"] for h in reversed(app.history) if h["role"] == "assistant"), "")
        answers.append({"q": q, "a": ans, "console": buf.getvalue()[-600:]})
    with contextlib.suppress(Exception):
        srv.proc.terminate()
    verdicts = {}
    for i, t in enumerate(answers):
        v = []
        for j in range(i):
            wi, wj = words(t["a"]), words(answers[j]["a"])
            if wi and len(wi & wj) / max(1, len(wi | wj)) >= 0.7:
                v.append(f"COPY of turn {j+1}")
        if degeneracy(t["a"]):
            v.append("LOOP")
        if re.search(r"(/ ){4,}|(\d+\. ){4,}|;s_[a-z0-9-]+\.txt\]|\[[a-z0-9_-]+\.txt\]", t["a"]):
            v.append("JUNK")
        verdicts[f"turn{i+1}"] = v
    ok1 = "lisbon" in answers[0]["a"].lower()
    ok4 = "391" in answers[3]["a"]
    abst3 = any(k in answers[2]["a"].lower() for k in ("no record", "don't have", "i don't know", "not in my records", "can't find"))
    tail3 = answers[2]["a"].lower().split("source")[0]
    invented3 = bool(re.search(r"\b(19|20)\d{2}\b|\b[A-Z]\. ?[A-Z]\. [A-Z][a-z]+", answers[2]["a"][40:]))
    summary = {"turn1_answered": ok1, "turn4_calc_right": ok4, "turn3_abstained": abst3, "turn3_invented_specifics": invented3,
               "fails": sum(len(v) for v in verdicts.values())}
    out = {"label": a.label, "model": a.model, "penalty": m.DECODE_REPEAT_PENALTY, "turns": answers, "verdicts": verdicts, "summary": summary}
    os.makedirs(os.path.join(ROOT, "evals", "results"), exist_ok=True)
    with io.open(os.path.join(ROOT, "evals", "results", f"{a.label}__multiturn.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for i, t in enumerate(answers):
        print(f"[{i+1}] {t['q']}\n    -> {t['a'][:160].replace(chr(10),' ')}\n    {verdicts[f'turn{i+1}'] or 'ok'}")
    print("summary:", json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())

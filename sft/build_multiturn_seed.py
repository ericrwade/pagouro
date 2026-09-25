"""Multi-turn and irrelevant-hit rows (D-93): the two data holes the first app smoke test of the 1B found.

Found 2026-09-25: in a conversation, the second question -- when it triggers pack_search -- was answered
with a verbatim copy of the FIRST answer, by every 1B variant (SFT A, SFT B, the soups, GRPO-3). Cause:
of the 165 training rows with a pack_search result, none sits in a second-or-later turn; the model has
never seen "earlier exchange -> new question -> tool result -> answer". Second hole: a pack hit that is
about something else (Bastiat for "who was Adam Smith") -- the model answers from it or dodges.

This builder makes, program-generated from existing seeds:
  (a) CONTEXT-SHIFT rows: 1-2 unrelated (user, assistant) exchanges from the style/abstention/calc seeds,
      then an existing tool row (harness_seed / toolresult_seed / synthetic_harness) verbatim. The lesson:
      the tool result belongs to the CURRENT question; earlier turns are context, not the answer.
  (b) IRRELEVANT-HIT rows: a known question (style_seed, with its answer) + a pack_search result holding a
      random passage from the shipped packs that has nothing to do with it; the assistant says the passage
      does not cover the question and answers from its own knowledge -- or, for an abstention-seed
      question, says so and abstains. The lesson: a hit is evidence only if it is about the question.

    python sft/build_multiturn_seed.py   -> sft/multiturn_seed.jsonl
"""
from __future__ import annotations

import glob
import io
import json
import os
import random
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SFT = os.path.join(ROOT, "sft")
OUT = os.path.join(SFT, "multiturn_seed.jsonl")
rng = random.Random(93)


def rows(path):
    return [json.loads(l) for l in io.open(path, encoding="utf-8") if l.strip()] if os.path.exists(path) else []


def qa_pairs():
    """(user, assistant) exchanges usable as unrelated earlier turns."""
    out = []
    for f in ("style_seed.jsonl", "calc_seed.jsonl", "spelling_seed.jsonl"):
        for r in rows(os.path.join(SFT, f)):
            if "question" in r and "answer" in r and 3 <= len(r["answer"].split()) <= 60:
                out.append((r["question"], r["answer"]))
    for r in rows(os.path.join(SFT, "abstention_seed.jsonl")):
        ms = r.get("messages", [])
        if len(ms) == 2 and ms[0]["role"] == "user":
            out.append((ms[0]["content"], ms[1]["content"]))
    return out


def tool_rows():
    out = []
    for f in ("harness_seed.jsonl", "toolresult_seed.jsonl", "synthetic_harness.jsonl"):
        for r in rows(os.path.join(SFT, f)):
            ms = r.get("messages")
            if ms and any(m["role"] == "tool" for m in ms) and ms[-1]["role"] == "assistant":
                out.append(ms)
    return out


def pack_passages(n=400):
    ps = []
    for f in glob.glob(os.path.join(ROOT, "packs", "*.txt")):
        text = io.open(f, encoding="utf-8", errors="replace").read()
        paras = [p.strip() for p in re.split(r"\n\s*\n", text) if 200 <= len(p.strip()) <= 700]
        rng.shuffle(paras)
        ps += [(os.path.basename(f), p) for p in paras[:n // 4]]
    rng.shuffle(ps)
    return ps


def main() -> int:
    pairs = qa_pairs()
    tools = tool_rows()
    passages = pack_passages()
    out = []
    # (a) context-shift: 500 rows
    for _ in range(500):
        base = rng.choice(tools)
        k = rng.choice((1, 1, 2))
        prefix = []
        for q, a in rng.sample(pairs, k):
            prefix += [{"role": "user", "content": q}, {"role": "assistant", "content": a}]
        sysm = [m for m in base if m["role"] == "system"]
        body = [m for m in base if m["role"] != "system"]
        out.append({"kind": "context-shift", "messages": sysm + prefix + body})
    # (b) irrelevant hit: 200 rows (150 known, 50 abstain)
    known = [(r["question"], r["answer"]) for r in rows(os.path.join(SFT, "style_seed.jsonl")) if "question" in r]
    abst = [(m[0]["content"], m[1]["content"]) for m in (r.get("messages", []) for r in rows(os.path.join(SFT, "abstention_seed.jsonl"))) if len(m) == 2]
    openers = ["The passage the search found is about something else and doesn't cover that. ",
               "That hit isn't about your question — it's a passage from {f}. ",
               "The pack result doesn't answer this; it's an unrelated paragraph from {f}. "]
    for i in range(150):
        q, a = rng.choice(known)
        f, p = rng.choice(passages)
        op = rng.choice(openers).format(f=f)
        out.append({"kind": "irrelevant-hit", "messages": [
            {"role": "user", "content": q},
            {"role": "tool", "content": f"pack_search: [{f}] {p[:400]}"},
            {"role": "assistant", "content": op + "From what I know: " + a}]})
    for i in range(50):
        q, a = rng.choice(abst)
        f, p = rng.choice(passages)
        op = rng.choice(openers).format(f=f)
        out.append({"kind": "irrelevant-hit-abstain", "messages": [
            {"role": "user", "content": q},
            {"role": "tool", "content": f"pack_search: [{f}] {p[:400]}"},
            {"role": "assistant", "content": op + a}]})
    rng.shuffle(out)
    with io.open(OUT, "w", encoding="utf-8") as fo:
        for r in out:
            fo.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"written {OUT}: {len(out)} rows (context-shift 500, irrelevant-hit 150 + 50 abstain); pairs {len(pairs)}, tool rows {len(tools)}, passages {len(passages)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

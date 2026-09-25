"""Abstention rows for the questions the model itself could not answer (O-45 #1, D-92 research plan).

sft/grpo_selfknow.jsonl labels each keyed question by the model's own 8-sample hit rate (soup70,
2026-09-25): 'unknowable_real' = it was right at most once in eight. Those are the questions where an
SFT should teach abstention, in the abstention seed's voice, because they are where THIS model is
guessing. Known questions ('real', >= 6/8) get no row: we have keys, not model answers, and the model
already answers them. Templates vary the phrasing so the fine-tune learns the act, not a sentence.

    python sft/build_selfknow_abstain_seed.py   -> sft/selfknow_abstain_seed.jsonl
"""
from __future__ import annotations

import io
import json
import os
import random
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sft", "grpo_selfknow.jsonl")
OUT = os.path.join(ROOT, "sft", "selfknow_abstain_seed.jsonl")
rng = random.Random(45)

TEMPLATES = [
    "I don't have a record of {t}. It may be real and simply outside what I was trained on; if you can point me to a source, I'll read it with you rather than guess.",
    "I can't tell you about {t} with any confidence — nothing I have covers it, and a made-up answer would be worse than none. If you have a page or a document on it, load it and I'll work from that.",
    "I don't know {t} well enough to answer. Rather than invent details, I'd rather say so. A source you trust would settle it; I can search the packs here if you'd like.",
    "No record of {t} on my side. That doesn't mean it doesn't exist — my training is limited and dated — only that I'd be guessing, and I don't do that.",
    "I'm not able to answer that reliably: {t} isn't something I have solid information on, and I won't fill the gap with plausible-sounding text. If you can give me a source, I'll use it.",
]


def subject(row: dict) -> str:
    t = (row.get("title") or "").strip()
    if t:
        return t
    q = row["prompt"].strip().rstrip("?.")
    q = re.sub(r"^(in one sentence, )?(who|what|tell me what|tell me about|when|where|which)\s+(is|was|are|were)?\s*", "", q, flags=re.I)
    return q or "that"


def main() -> int:
    rows = [json.loads(l) for l in io.open(SRC, encoding="utf-8") if l.strip()]
    unknown = [r for r in rows if r.get("kind") == "unknowable_real" and "self_hits" in r]
    out = []
    for r in unknown:
        t = subject(r)
        ans = rng.choice(TEMPLATES).format(t=t)
        out.append({"kind": "selfknow-abstain", "question": r["prompt"], "answer": ans, "self_hits": r["self_hits"]})
    with io.open(OUT, "w", encoding="utf-8") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print(f"written {OUT}: {len(out)} abstention rows from {len(unknown)} model-unknown questions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

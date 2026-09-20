"""D-68 (iii): teach the model to match the user's spelling register, not to pick one.

Takes the existing hand-written and program-generated SFT conversations (not the router rows and
not tool turns), makes a British-spelled copy of each conversation whose USER turn changes under
the swap (so the cue is in the question), and writes sft/spelling_seed.jsonl. American-spelled
originals stay where they are; the pair teaches "answer in the register you were asked in".
Also emits a small set of paired minimal conversations built from a fixed template list, both
registers, so the behaviour is taught even where the seed sets have few marked words.

    python sft/build_spelling_seed.py          -> sft/spelling_seed.jsonl (+ counts printed)
"""

from __future__ import annotations

import io
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))
from spelling import to_british, to_american, register  # noqa: E402

SOURCES = ["abstention_seed.jsonl", "crypto_synthetic.jsonl", "synthesis_seed.jsonl", "harness_seed.jsonl", "synthetic_harness.jsonl", "memory_seed.jsonl", "calc_seed.jsonl"]

# Paired minimal conversations: the answer is short and uses marked words; both registers emitted.
TEMPLATES = [
    ("What colour goes well with grey for a bedroom wall?",
     "Soft colours work with grey: a pale blue, a warm cream, or a muted green. Grey takes most colours; keep the second one lighter than the grey so the room does not go dull."),
    ("How do I organise a small kitchen?",
     "Organise by use: the things you touch daily at counter height, the rest above or below. Group like with like, label the containers, and clear one drawer for the odd items."),
    ("What is the centre of gravity of a uniform rod?",
     "The centre of gravity of a uniform rod is at its midpoint, halfway along its length. That is where it balances."),
    ("Is aluminium a good conductor of heat?",
     "Yes. Aluminium conducts heat well, better than steel and about half as well as copper, which is why it is used for cookware and heat sinks."),
    ("How many metres are in a kilometre?",
     "There are 1,000 metres in a kilometre."),
    ("What does a theatre's dress circle refer to?",
     "In a theatre the dress circle is the first tier of seats above the stalls, traditionally the best seats after the front stalls."),
    ("Why does bread go mouldy faster in summer?",
     "Mould grows faster in warm, humid air, so bread goes mouldy sooner in summer. Keep it cool and dry, or freeze what you will not eat in two days."),
    ("What is the honour system?",
     "An honour system is a rule that trusts people to comply without being watched, such as paying for goods left at an unattended stall."),
    ("How do I recognise a good neighbour?",
     "A good neighbour is considerate: keeps noise down, returns what they borrow, and tells you before doing anything that affects your side of the fence."),
    ("What is the flavour difference between brown and white sugar?",
     "Brown sugar contains molasses, which gives it a caramel flavour and more moisture; white sugar is plain sweetness. Brown sugar makes softer, darker baked goods."),
    ("Which is heavier, a litre of water or a litre of oil?",
     "A litre of water is heavier. Oil is less dense, about 0.92 kilograms per litre against water's 1.0, which is why oil floats."),
    ("How should I analyse a poem I do not understand?",
     "Read it aloud twice, mark the words that repeat, note where the tone shifts, and say in one sentence what it seems to be about; then check that sentence against the lines that do not fit."),
    ("What is a catalogue raisonné?",
     "A catalogue raisonné is a complete, annotated list of all the known works of an artist, with each work's description, provenance and history."),
    ("How do I cancel a travelling habit of overpacking?",
     "Lay out everything you think you need, then remove a third. Pack for the days you will actually be travelling, not for every possibility, and plan to wash clothes once."),
    ("What is the behaviour of a gas when it is heated in a sealed container?",
     "In a sealed container the gas cannot expand, so heating it raises its pressure in proportion to its absolute temperature. Heat it enough and the container fails."),
    ("What favourite tools do woodworkers recommend for a beginner?",
     "A sharp chisel, a marking gauge, a combination square, a block plane and a good saw. Buy fewer, better tools and learn to sharpen them."),
    ("How do I apologise well?",
     "Say what you did, say that it was wrong, say what you will do differently, and stop. Do not explain why you did it, and do not ask to be forgiven in the same breath."),
    ("What is the difference between a metre and a yard?",
     "A metre is a little longer than a yard: one yard is 0.9144 metres, so a metre is about 39.4 inches against the yard's 36."),
    ("What is the labour theory of value?",
     "The labour theory of value holds that the value of a good comes from the labour needed to make it. It was central to classical economics and to Marx; modern economics mostly replaced it with a theory based on marginal utility."),
    ("Why is the sky a paler colour near the horizon?",
     "Light from near the horizon travels through more air, so more of the blue is scattered away before it reaches you and the remaining light looks paler and whiter."),
]


def convs_from(path: str) -> list[list[dict]]:
    out = []
    if not os.path.exists(path):
        return out
    for line in io.open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        if d.get("kind") == "router":
            continue
        msgs = d["messages"] if "messages" in d else [{"role": "user", "content": d["question"]},
                                                       {"role": "assistant", "content": d["answer"]}]
        if any(m["role"] == "assistant" and m["content"].lstrip().startswith("{\"tool\"") for m in msgs):
            continue
        out.append(msgs)
    return out


def main() -> int:
    rng = random.Random(68)
    rows, n_seen, n_user_changed, n_both = [], 0, 0, 0
    for src in SOURCES:
        for msgs in convs_from(os.path.join(ROOT, "sft", src)):
            n_seen += 1
            uk = []
            user_changed = asst_changed = False
            for m in msgs:
                if m["role"] in ("user", "assistant"):
                    t = to_british(m["content"])
                    if t != m["content"]:
                        if m["role"] == "user":
                            user_changed = True
                        else:
                            asst_changed = True
                    uk.append({"role": m["role"], "content": t})
                else:
                    uk.append(dict(m))          # tool / system turns untouched
            if user_changed:
                n_user_changed += 1
                n_both += asst_changed
                rows.append({"kind": "spelling", "register": "british", "source": src, "messages": uk})
    for q, a in TEMPLATES:
        rows.append({"kind": "spelling", "register": "british", "source": "template",
                     "messages": [{"role": "user", "content": q}, {"role": "assistant", "content": a}]})
        rows.append({"kind": "spelling", "register": "american", "source": "template",
                     "messages": [{"role": "user", "content": to_american(q)}, {"role": "assistant", "content": to_american(a)}]})
    rng.shuffle(rows)
    out = os.path.join(ROOT, "sft", "spelling_seed.jsonl")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    marked = sum(1 for r in rows if register(" ".join(m["content"] for m in r["messages"] if m["role"] == "assistant")) != (0, 0))
    print(f"seed conversations seen {n_seen:,}; user turn changed under the swap {n_user_changed:,} (answer changed too: {n_both:,}); "
          f"templates {2 * len(TEMPLATES)}; written {len(rows):,} rows, {marked:,} with a marked word in the answer -> {os.path.relpath(out, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

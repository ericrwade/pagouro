"""Hand-built SFT seed for level-1 memory (O-23): teach the router that questions about the
owner's own life go to pack_search (their notes and transcripts live there), and teach the
answer turn to use a hit labelled YOUR OWN WORDS -- briefly, citing that the owner said it --
and to say "no record in your notes" when the hits do not cover it.

Facts here are DISJOINT from evals/memory.json (no Ruby, Lisbon, bluefern42, Honda, June 14,
penicillin, Thursday book club, Okafor). Every row is program-generated from templates and is
labelled synthetic; nothing pre-2022 is claimed for SFT data (D-34).

    python sft/build_memory_seed.py      -> sft/memory_seed.jsonl
"""

from __future__ import annotations

import io
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))
from prompts import ROUTER_PROMPT, SYSTEM_PROMPT  # noqa: E402

rng = random.Random(23)

# (what the owner said earlier, the later question, the short answer)
FACTS = [
    ("my cat is called Pepper and he is fourteen", "What's my cat's name?", "You told me your cat is called Pepper."),
    ("I drink green tea in the afternoon, never coffee after noon", "Do I drink coffee in the afternoon?", "No. You said you drink green tea in the afternoon and no coffee after noon."),
    ("my brother Tomas lives in Kraków", "Where does my brother live?", "You said your brother Tomas lives in Kraków."),
    ("the gate code for the allotment is 4471", "What's the gate code for the allotment?", "You told me the allotment gate code is 4471."),
    ("I'm planting garlic and leeks in the back bed this autumn", "What am I planting in the back bed?", "Garlic and leeks, you said, in the back bed this autumn."),
    ("my bike is a 2016 Trek FX2 and the chain is a KMC X8", "What chain does my bike take?", "You noted your bike, a 2016 Trek FX2, takes a KMC X8 chain."),
    ("Mum's birthday is the 3rd of March", "When is Mum's birthday?", "You told me it's the 3rd of March."),
    ("I'm lactose intolerant", "Is there anything I can't eat?", "You said you're lactose intolerant."),
    ("choir practice is Tuesdays at seven at St Anne's hall", "When is choir practice?", "Tuesdays at seven, at St Anne's hall, according to your note."),
    ("my dentist is Dr Feld on Harbour Street", "Who is my dentist?", "You told me your dentist is Dr Feld on Harbour Street."),
    ("the boiler service is due every October", "When is the boiler service due?", "Every October, you said."),
    ("my daughter Ines is learning the cello", "Which instrument is my daughter learning?", "The cello -- you mentioned Ines is learning it."),
    ("we decided to repaint the kitchen in sage green", "What colour did we choose for the kitchen?", "Sage green, per your note."),
    ("the car insurance renews on the 20th of January", "When does the car insurance renew?", "You told me the 20th of January."),
    ("I prefer short answers unless I ask for detail", "How do I like my answers?", "Short, you said, unless you ask for detail."),
    ("our neighbour's dog is called Biscuit", "What's the neighbour's dog called?", "Biscuit, according to what you told me."),
    ("my shoe size is 43 in EU sizing", "What's my shoe size?", "You said 43, EU sizing."),
    ("the spare key is under the blue pot by the shed", "Where is the spare key?", "You told me it's under the blue pot by the shed."),
    ("I'm training for the half marathon in April", "What am I training for?", "The half marathon in April, you said."),
    ("my favourite bread recipe uses 500 g flour and 10 g salt", "How much salt goes in my bread recipe?", "10 g, in your recipe with 500 g of flour."),
]

# Personal questions with NOTHING in memory: the honest answer is "no record".
UNKNOWN_Q = [
    "What's my sister's middle name?", "Which gym did I join?", "When did I last change the smoke alarm battery?",
    "What was the name of the hotel in Porto?", "How much did I pay for the fridge?", "What's my blood type?",
]

# Statements that need NO tool (routing balance): the owner is telling, not asking.
NO_TOOL = [
    "I'm tired today.", "Remember that I hate cilantro.", "Thanks, that helps.", "Just thinking out loud here.",
    "Let me tell you about my week.", "I finished the book you mentioned.", "It rained all morning.",
    "What is 12 times 9?", "Explain what a mutex is.", "What day is it today?",
]
NO_TOOL_ROUTE = {"What is 12 times 9?": ("calc", "12*9"), "What day is it today?": ("time", ""),
                 "Explain what a mutex is.": ("none", "")}

PACK_NOISE = [
    "[mill-on-liberty.txt] The only freedom which deserves the name, is that of pursuing our own good in our own way",
    "[usda-home-canning-2015.txt] Process jars in a boiling-water canner for the time listed in the table",
    "[us-fhwa-mutcd-2009.txt] Section 2B.03 Size of Regulatory Signs",
]


def router_row(user: str, tool: str, arg: str) -> dict:
    return {"kind": "memory_router", "synthetic": True, "messages": [
        {"role": "system", "content": ROUTER_PROMPT},
        {"role": "user", "content": user},
        {"role": "assistant", "content": json.dumps({"tool": tool, "arguments": arg}, separators=(",", ":"))}]}


def answer_row(user: str, tool_result: str, assistant: str) -> dict:
    date = f"2027-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
    return {"kind": "memory_answer", "synthetic": True, "messages": [
        {"role": "system", "content": SYSTEM_PROMPT.format(date=date)},
        {"role": "user", "content": user},
        {"role": "tool", "content": f"pack_search: {tool_result}"},
        {"role": "assistant", "content": assistant}]}


def main() -> int:
    rows = []
    for told, ask, ans in FACTS:
        rows.append(router_row(ask, "pack_search", ask.rstrip("?")))
        day = f"2027-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
        hit = f"[YOUR OWN WORDS, from remembered.txt] {day}: {told}"
        noise = rng.sample(PACK_NOISE, 2)
        order = [hit] + noise if rng.random() < 0.6 else [noise[0], hit, noise[1]]
        rows.append(answer_row(ask, "\n\n".join(order), ans))
    for q in UNKNOWN_Q:
        rows.append(router_row(q, "pack_search", q.rstrip("?")))
        rows.append(answer_row(q, "\n\n".join(rng.sample(PACK_NOISE, 2)),
                               "I have no record of that in your notes or earlier chats. If you tell me, /remember will keep it."))
        rows.append(answer_row(q, "NO_MATCH: nothing in the loaded packs covers this.",
                               "I have no record of that. Nothing in your notes or the packs covers it."))
    for s in NO_TOOL:
        tool, arg = NO_TOOL_ROUTE.get(s, ("none", ""))
        rows.append(router_row(s, tool, arg))
    rng.shuffle(rows)
    out = os.path.join(ROOT, "sft", "memory_seed.jsonl")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"wrote {out}: {len(rows)} rows {kinds}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Convert the synthetic crypto Q&A into tutor item-bank format, citing the
ledger row added for them (crypto-synthetic-deepseek), per tutor/item_bank_schema.md's
rule that every item must trace to a source that already cleared the ledger.
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sft", "crypto_synthetic.jsonl")
OUT = os.path.join(ROOT, "tutor", "items", "crypto_30.jsonl")

with io.open(SRC, encoding="utf-8") as f, io.open(OUT, "w", encoding="utf-8", newline="\n") as out:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        item = {
            "id": f"crypto-synth-{i:03d}",
            "topic": "technology-and-crypto",
            "question": d["question"],
            "reference_answer": d["answer"],
            "explanation": d["passage"],
            "difficulty": 1 if len(d["answer"]) < 150 else 2,
            "source": "crypto-synthetic-deepseek",
            "source_locator": d["source_slug"],
        }
        out.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"wrote {OUT}")

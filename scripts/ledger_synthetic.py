"""Add or refresh the corpus.json row for sft/synthetic_harness.jsonl.

Run after (or during) scripts/generate_synthetic_harness.py. Idempotent: the row is
replaced by slug. The hash and counts are measured from the file, never typed in.

    python scripts/ledger_synthetic.py
"""

from __future__ import annotations

import collections
import hashlib
import io
import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sft", "synthetic_harness.jsonl")
LEDGER = os.path.join(ROOT, "corpus.json")
SLUG = "harness-synthetic-qwen2.5-7b"


def main() -> int:
    if not os.path.exists(SRC):
        raise SystemExit(f"missing {SRC}")
    rows = [json.loads(l) for l in io.open(SRC, encoding="utf-8") if l.strip()]
    kinds = collections.Counter(r["kind"] for r in rows)
    h = hashlib.sha256()
    with open(SRC, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    now = datetime.now(timezone.utc)
    row = {
        "slug": SLUG,
        "name": "Synthetic harness SFT conversations, generated locally by Qwen2.5-7B-Instruct",
        "license": "Apache-2.0 (generator: Qwen/Qwen2.5-7B-Instruct-GGUF, q4_k_m); the prompts and validation rules are in scripts/generate_synthetic_harness.py",
        "generation_method": "D-30: open weights run LOCALLY via llama-server on the EVO-X2, never an API. Classes: router decisions (label by construction), tool answers with the tool EXECUTED for real (calc, BM25 pack search over the shipped packs, simulated clock/file/note), grounded passage Q&A, invented-entity refusals, general-knowledge answers (verifier pass at temperature 0; answers leaning on precise figures dropped), comparisons (verified), multi-turn dialogues (invented specifics forbidden; number-heavy replies dropped). Every row deduplicated against all other SFT files and checked for overlap with the frozen evals (bluff, calibration, deflection, tooluse).",
        "published_before_generative_ai": False,
        "note": "Synthetic, not scraped. A 7B teacher states wrong facts occasionally; the filters reduce but do not eliminate that, which is why the answered-real and bluff rates are measured on the frozen suite rather than assumed. Excluded from any pre-2022 claim by construction.",
        "retrieved": now.date().isoformat(),
        "retrieved_utc": now.isoformat(timespec="seconds"),
        "documents": len(rows),
        "by_kind": dict(sorted(kinds.items())),
        "bytes": os.path.getsize(SRC),
        "sha256_processed": h.hexdigest(),
        "file": "sft/synthetic_harness.jsonl",
        "slice": "SFT (synthetic, tool-executed, filtered)",
    }
    with io.open(LEDGER, encoding="utf-8") as f:
        ledger = json.load(f)
    sources = ledger["sources"]
    sources[:] = [s for s in sources if s.get("slug") != SLUG] + [row]
    with io.open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"ledger row {SLUG}: {len(rows)} conversations {dict(kinds)}, sha256 {h.hexdigest()[:12]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

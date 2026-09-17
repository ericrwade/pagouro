"""Validate the tutor item bank against its schema and against corpus.json.

The one rule that must never be violated silently: every item's `source` must be
a slug that actually exists in the corpus ledger. The tutor inherits Pagouro's
provenance standard rather than keeping a looser one of its own -- an item citing
a source that was never cleared is exactly the kind of unearned claim the whole
project exists to avoid making.

    python tutor/validate_items.py
"""

from __future__ import annotations

import glob
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS_DIR = os.path.join(ROOT, "tutor", "items")
LEDGER = os.path.join(ROOT, "corpus.json")

REQUIRED = ["id", "topic", "question", "reference_answer", "explanation", "difficulty", "source"]
VALID_TOPICS = {
    "money-and-economics", "property-law-and-rights",
    "practical-numeracy-and-finance", "liberty-canon", "technology-and-crypto",
}


def main() -> int:
    with io.open(LEDGER, encoding="utf-8") as f:
        ledger = json.load(f)
    known_sources = {s["slug"] for s in ledger["sources"]}

    files = sorted(glob.glob(os.path.join(ITEMS_DIR, "*.jsonl")))
    if not files:
        print(f"no item files found in {os.path.relpath(ITEMS_DIR, ROOT)}")
        return 1

    seen_ids = set()
    errors = []
    n_items = 0
    by_topic: dict[str, int] = {}
    by_source: dict[str, int] = {}

    for fp in files:
        with io.open(fp, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                loc = f"{os.path.basename(fp)}:{lineno}"
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as e:
                    errors.append(f"{loc}: invalid JSON ({e})")
                    continue

                n_items += 1
                for field in REQUIRED:
                    if field not in item or item[field] in (None, ""):
                        errors.append(f"{loc}: missing required field '{field}'")

                iid = item.get("id")
                if iid:
                    if iid in seen_ids:
                        errors.append(f"{loc}: duplicate id '{iid}'")
                    seen_ids.add(iid)

                topic = item.get("topic")
                if topic and topic not in VALID_TOPICS:
                    errors.append(f"{loc}: unknown topic '{topic}' (not in {sorted(VALID_TOPICS)})")
                if topic:
                    by_topic[topic] = by_topic.get(topic, 0) + 1

                diff = item.get("difficulty")
                if diff is not None and diff not in (1, 2, 3):
                    errors.append(f"{loc}: difficulty must be 1, 2 or 3, got {diff!r}")

                source = item.get("source")
                if source and source not in known_sources:
                    errors.append(
                        f"{loc}: source '{source}' is NOT in corpus.json's ledger. "
                        f"An item cannot cite a source that was never cleared."
                    )
                if source:
                    by_source[source] = by_source.get(source, 0) + 1

    print(f"checked {n_items} items across {len(files)} file(s)")
    print(f"\nby topic:")
    for t in sorted(VALID_TOPICS):
        print(f"  {t:<32} {by_topic.get(t, 0)}")
    print(f"\nby source:")
    for s, n in sorted(by_source.items(), key=lambda kv: -kv[1]):
        print(f"  {s:<45} {n}")

    if errors:
        print(f"\n{len(errors)} ERROR(S):")
        for e in errors:
            print(f"  {e}")
        return 1
    print(f"\nPASS: all {n_items} items valid, every source traceable to corpus.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

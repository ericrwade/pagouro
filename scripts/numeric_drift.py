"""Numeric drift between two OCR renderings of the same work (D-66 audit).

Numbers are where OCR errors become facts ("P = 45 watts" for 4.5). For each pair of files,
compare the multisets of numeric strings and report how many numbers appear in only one side.
The tool never corrects anything; it produces a review list.

    python scripts/numeric_drift.py data/raw/usgov/neets-13-digital.txt data/raw/usgov/usgov-neets-13-reocr.md
"""

from __future__ import annotations

import collections
import io
import re
import sys

NUM = re.compile(r"(?<![\w.])[-+]?\d[\d,]*(?:\.\d+)?(?![\w])")


def numbers(path: str) -> collections.Counter:
    text = io.open(path, encoding="utf-8", errors="replace").read()
    text = re.sub(r"<!-- page \d+ -->", " ", text)
    return collections.Counter(n.replace(",", "") for n in NUM.findall(text))


def main() -> int:
    old, new = sys.argv[1], sys.argv[2]
    a, b = numbers(old), numbers(new)
    only_old, only_new = a - b, b - a
    shared = sum((a & b).values())
    tot_old, tot_new = sum(a.values()), sum(b.values())
    print(f"{old}: {tot_old:,} numeric strings | {new}: {tot_new:,}")
    print(f"shared {shared:,}; only in old {sum(only_old.values()):,}; only in new {sum(only_new.values()):,}")
    print(f"disagreement (old side): {100 * sum(only_old.values()) / max(1, tot_old):.1f}%  (new side): {100 * sum(only_new.values()) / max(1, tot_new):.1f}%")
    print("most frequent numbers only in the old OCR:", only_old.most_common(12))
    print("most frequent numbers only in the new OCR:", only_new.most_common(12))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

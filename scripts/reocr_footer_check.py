"""Sanity check on a re-OCR'd work: printed page numbers must run in order (D-66 audit).

Batched vision-OCR can attach the wrong page's content to a leaf (found 2026-09-20: USDA canning
leaves 94-95 carried footers 3-8/3-9 and the wrong process times). The page images print their
own page numbers, so a footer that repeats or runs backwards marks a suspect leaf. Run on the pod's
per-page folder or on the assembled <item>.md.

    python scripts/reocr_footer_check.py runs/runpod/reocr/NEETSModule01.md
"""

from __future__ import annotations

import io
import re
import sys

FOOT = re.compile(r"^\s*(?:(\d{1,2})-(\d{1,3})|(\d{1,4}))\s*$", re.M)   # "3-12" or "412"
HEAD = re.compile(r"\bPage\s+(\d{1,4})\b")                                # MUTCD-style running head "2009 Edition   Page 259"


def pages(path: str) -> list[tuple[int, str]]:
    text = io.open(path, encoding="utf-8", errors="replace").read()
    parts = re.split(r"<!-- page (\d+) -->", text)
    return [(int(parts[i]), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


def footer(page_text: str):
    tail = page_text.strip().splitlines()[-4:] if page_text.strip() else []
    head = page_text.strip().splitlines()[:3] if page_text.strip() else []
    for line in reversed(tail + head):
        m = FOOT.match(line)
        if m:
            if m.group(1):
                return int(m.group(1)), int(m.group(2))
            return 0, int(m.group(3))
    m = HEAD.search(page_text[:200])
    if m:
        return 0, int(m.group(1))
    return None


def main() -> int:
    path = sys.argv[1]
    seq = [(leaf, footer(t)) for leaf, t in pages(path)]
    got = [(leaf, f) for leaf, f in seq if f]
    suspects = []
    for k in range(1, len(got)):
        (l0, f0), (l1, f1) = got[k - 1], got[k]
        if f1[0] == f0[0] and f1[1] <= f0[1] and (l1 - l0) <= 3:      # same chapter, number not increasing
            suspects.append((l1, f1, l0, f0))
    print(f"{path}: {len(seq)} pages, {len(got)} with a printed page number, {len(suspects)} out-of-order footers")
    for l1, f1, l0, f0 in suspects[:40]:
        print(f"  leaf {l1} prints {f1[0]}-{f1[1] if f1[0] else f1[1]} after leaf {l0} printed {f0[0]}-{f0[1] if f0[0] else f0[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

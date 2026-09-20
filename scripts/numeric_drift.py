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


def stream(path: str) -> list[tuple[str, str, int]]:
    """Ordered (number, context, page) triples. Page comes from <!-- page N --> markers when present."""
    text = io.open(path, encoding="utf-8", errors="replace").read()
    out, page = [], 0
    pos = 0
    marks = [(m.start(), int(m.group(1))) for m in re.finditer(r"<!-- page (\d+) -->", text)]
    mi = 0
    for m in NUM.finditer(text):
        while mi < len(marks) and marks[mi][0] < m.start():
            page = marks[mi][1]; mi += 1
        ctx = text[max(0, m.start() - 40): m.end() + 40].replace("\n", " ")
        out.append((m.group(0).replace(",", ""), ctx, page))
    return out


def near_miss(x: str, y: str) -> str | None:
    """Why two numbers look like the same number misread: decimal point moved/dropped, one digit off,
    two digits swapped. Returns the reason or None."""
    dx, dy = x.replace(".", "").lstrip("+-"), y.replace(".", "").lstrip("+-")
    if x == y:
        return None
    if dx == dy:
        return "decimal point"
    if len(dx) == len(dy) and sum(c != d for c, d in zip(dx, dy)) == 1:
        return "one digit"
    if len(dx) == len(dy) and sorted(dx) == sorted(dy):
        return "digits swapped"
    if abs(len(dx) - len(dy)) == 1 and (dx in dy or dy in dx):
        return "one digit missing"
    return None


def context_match(c1: str, c2: str) -> float:
    """Jaccard overlap of the non-numeric words around two numbers (HTML/markdown stripped)."""
    def words(c: str) -> set[str]:
        c = re.sub(r"<[^>]+>|[*_#|!\[\]()]", " ", c)
        return {w for w in re.findall(r"[a-z]{3,}", c.lower())}
    w1, w2 = words(c1), words(c2)
    return len(w1 & w2) / max(1, len(w1 | w2))


def conflicts(old: str, new: str, limit: int = 60) -> int:
    """Align the two ordered number streams and list replacements that look like misreads."""
    import difflib
    a, b = stream(old), stream(new)
    sm = difflib.SequenceMatcher(a=[x[0] for x in a], b=[y[0] for y in b], autojunk=False)
    found = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "replace":
            continue
        for x, y in zip(a[i1:i2], b[j1:j2]):     # positional pairing inside the replaced run
            why = near_miss(x[0], y[0])
            if why and context_match(x[1], y[1]) >= 0.5:   # the words around both numbers must mostly agree
                found.append((why, x, y))
    by_reason = collections.Counter(w for w, _, _ in found)
    print(f"aligned {sm.ratio():.3f}; near-miss replacements: {len(found)} {dict(by_reason)}")
    for why, x, y in found[:limit]:
        print(f"  [{why}] old {x[0]!r} -> new {y[0]!r}  (new page {y[2]})\n      old: …{x[1].strip()}…\n      new: …{y[1].strip()}…")
    return len(found)


def main() -> int:
    if "--conflicts" in sys.argv:
        args = [x for x in sys.argv[1:] if x != "--conflicts"]
        return 0 if conflicts(args[0], args[1]) >= 0 else 1
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

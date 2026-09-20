"""Scale a recipe's quantities: "double: 2 cups flour, 1 1/2 tsp salt, 3 eggs", "halve: ...",
"scale 1.5x: ...", "for 6 instead of 4: ...". Quantities may be integers, decimals, fractions
(1/2) or mixed numbers (1 1/2). Nothing is converted between units here; use unit_convert."""

from __future__ import annotations

import re
from fractions import Fraction

DESCRIPTION = "scale recipe quantities: 'double: 2 cups flour, 1/2 tsp salt' or 'for 6 instead of 4: ...'"
NEEDS_ACT = False
TRIGGER = (r"^(?=.*\d)(?=.*(:|\b(cups?|tsp|tbsp|teaspoons?|tablespoons?|eggs?|oz|lbs?|g|kg|ml|qt|pinch)\b))"
           r"(?=.*\b(double|triple|halve|halved|half|quarter|scale|\d+(?:\.\d+|/\d+)?\s*x|\d+ times|for \d+ instead of \d+|"
           r"serves?|recipe|batch|bigger|smaller)\b)")

QTY = re.compile(r"(?<![\w/])(\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)(?![\w/])")
WORDS = {"double": 2, "triple": 3, "halve": Fraction(1, 2), "half": Fraction(1, 2), "quarter": Fraction(1, 4)}


def factor(head: str) -> Fraction | None:
    h = head.lower().strip()
    for w, f in WORDS.items():
        if w in h:
            return Fraction(f)
    m = re.search(r"for\s+(\d+(?:\.\d+)?)\s+(?:instead of|rather than|not)\s+(\d+(?:\.\d+)?)", h)
    if m:
        return Fraction(m.group(1)) / Fraction(m.group(2))
    m = re.search(r"(?:serves|for|feeds|makes)\s+(\d+).*?\b(?:for|to|into)\s+(\d+)\b", h)   # "serves 4, make it for 6"
    if m:
        return Fraction(m.group(2)) / Fraction(m.group(1))
    m = re.search(r"(\d+/\d+|\d+(?:\.\d+)?)\s*(?:x|times)", h)     # fraction branch first, or '3/2' reads as 3
    if m:
        return Fraction(m.group(1))
    m = re.search(r"(?:scale|multiply)\s+(?:by\s+)?(\d+/\d+|\d+(?:\.\d+)?)", h)
    if m:
        return Fraction(m.group(1))
    return None


def to_frac(s: str) -> Fraction:
    s = s.strip()
    if " " in s:
        a, b = s.split()
        return Fraction(a) + Fraction(b)
    return Fraction(s)


def nice(f: Fraction) -> str:
    """Kitchen-friendly: whole numbers plain, else mixed number when the denominator is 2,3,4,8; else decimal."""
    if f.denominator == 1:
        return str(f.numerator)
    if f.denominator in (2, 3, 4, 8, 16):
        whole, rem = divmod(f.numerator, f.denominator)
        return (f"{whole} " if whole else "") + f"{rem}/{f.denominator}"
    return f"{float(f):.2f}".rstrip("0").rstrip(".")


def run(argument: str, app=None) -> str:
    t = argument.strip()
    head, sep, body = t.partition(":")
    if not sep:
        m = re.match(r"(double|triple|halve|half|quarter|scale[^,]*?|for \d+ instead of \d+)\s+(.*)", t, re.I)
        if not m:
            return "NO_MATCH: say '<double|halve|1.5x|for 6 instead of 4>: <ingredient list>'"
        head, body = m.group(1), m.group(2)
    k = factor(head)
    if k is None:
        return f"NO_MATCH: I could not read a scaling factor in '{head.strip()}'."
    lines = [x.strip() for x in re.split(r",|;|\n", body) if x.strip()]
    if not lines:
        return "NO_MATCH: no ingredients after the colon."
    out = []
    for ln in lines:
        def sub(m):
            return nice(to_frac(m.group(1)) * k)
        new = QTY.sub(sub, ln, count=1)
        out.append(new + ("" if QTY.search(ln) else "  (no quantity found; left as written)"))
    return f"scaled x{nice(k)}:\n" + "\n".join(out)

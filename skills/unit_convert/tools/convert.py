"""Unit conversion: "12 km to miles", "350 F in C", "2 cups to ml", "5 lb to kg", "1.5 GB to MB".
Pure table + arithmetic; no model judgement inside. Unknown unit -> says so, converts nothing."""

from __future__ import annotations

import re

DESCRIPTION = "convert a quantity between units, e.g. '12 km to miles' or '350 F to C'"
NEEDS_ACT = False
TRIGGER = (r"^(?=.*(\d|\bhalf\b|\bquarter\b))"                      # a quantity ...
           r"(?=.*\b(km|mi|miles?|kilomet\w*|lbs?|pounds?|kg|kilos?|kilogram\w*|oz|ounces?|cups?|ml|millilit\w*|litres?|"
           r"liters?|tbsp|tsp|tablespoons?|teaspoons?|°\s?[cf]|degrees? [cf]|celsius|fahrenheit|kelvin|inch\w*|feet|foot|"
           r"ft|cm|mm|metres?|meters?|yards?|gb|mb|kb|tb|gib|mib|mph|kph|km/h|knots?|parsecs?)\b)"   # ... a unit word ...
           r"(?=.*(\bconvert\b|\b(to|in|into|as|is|are)\b))")            # ... and a link word. Time units are left to calc (frozen suite).

# canonical base per dimension; factor = how many base units in one of this unit
UNITS = {
    # length (m)
    "mm": ("length", 0.001), "cm": ("length", 0.01), "m": ("length", 1.0), "km": ("length", 1000.0),
    "in": ("length", 0.0254), "ft": ("length", 0.3048), "yd": ("length", 0.9144), "mi": ("length", 1609.344),
    "nmi": ("length", 1852.0),
    # mass (kg)
    "mg": ("mass", 1e-6), "g": ("mass", 0.001), "kg": ("mass", 1.0), "t": ("mass", 1000.0),
    "oz": ("mass", 0.028349523125), "lb": ("mass", 0.45359237), "st": ("mass", 6.35029318),
    # volume (l)
    "ml": ("volume", 0.001), "l": ("volume", 1.0), "tsp": ("volume", 0.00492892159375),
    "tbsp": ("volume", 0.01478676478125), "floz": ("volume", 0.0295735295625), "cup": ("volume", 0.2365882365),
    "pt": ("volume", 0.473176473), "qt": ("volume", 0.946352946), "gal": ("volume", 3.785411784),
    # data (byte)
    "b": ("data", 1.0), "kb": ("data", 1000.0), "mb": ("data", 1e6), "gb": ("data", 1e9), "tb": ("data", 1e12),
    "kib": ("data", 1024.0), "mib": ("data", 1024.0 ** 2), "gib": ("data", 1024.0 ** 3),
    # time (s)
    "s": ("time", 1.0), "min": ("time", 60.0), "h": ("time", 3600.0), "day": ("time", 86400.0), "week": ("time", 604800.0),
    # speed (m/s)
    "mps": ("speed", 1.0), "kph": ("speed", 1000.0 / 3600), "mph": ("speed", 1609.344 / 3600), "kn": ("speed", 1852.0 / 3600),
    # temperature handled separately
    "c": ("temp", 0), "f": ("temp", 0), "k": ("temp", 0),
}
ALIASES = {
    "millimeter": "mm", "millimetre": "mm", "centimeter": "cm", "centimetre": "cm", "meter": "m", "metre": "m",
    "kilometer": "km", "kilometre": "km", "inch": "in", "inches": "in", "foot": "ft", "feet": "ft", "yard": "yd",
    "mile": "mi", "nautical mile": "nmi", "milligram": "mg", "gram": "g", "kilogram": "kg", "kilo": "kg",
    "tonne": "t", "ton": "t", "ounce": "oz", "pound": "lb", "stone": "st", "milliliter": "ml", "millilitre": "ml",
    "liter": "l", "litre": "l", "teaspoon": "tsp", "tablespoon": "tbsp", "fluid ounce": "floz", "fl oz": "floz",
    "cups": "cup", "pint": "pt", "quart": "qt", "gallon": "gal", "byte": "b", "kilobyte": "kb", "megabyte": "mb",
    "gigabyte": "gb", "terabyte": "tb", "kibibyte": "kib", "mebibyte": "mib", "gibibyte": "gib", "second": "s",
    "sec": "s", "minute": "min", "hour": "h", "hr": "h", "days": "day", "weeks": "week", "m/s": "mps",
    "km/h": "kph", "kmh": "kph", "mi/h": "mph", "knot": "kn", "celsius": "c", "centigrade": "c", "fahrenheit": "f",
    "kelvin": "k", "°c": "c", "°f": "f", "degrees c": "c", "degrees f": "f", "deg c": "c", "deg f": "f",
}
NUM = r"[-+]?\d+(?:[.,]\d+)?"


def canon(u: str) -> str | None:
    u = u.strip().lower().rstrip(".")
    if u in UNITS:
        return u
    if u in ALIASES:
        return ALIASES[u]
    if u.endswith("s") and u[:-1] in ALIASES:
        return ALIASES[u[:-1]]
    if u.endswith("es") and u[:-2] in ALIASES:
        return ALIASES[u[:-2]]
    if u.endswith("s") and u[:-1] in UNITS:
        return u[:-1]
    return None


def temp(v: float, a: str, b: str) -> float:
    k = {"c": v + 273.15, "f": (v - 32) * 5 / 9 + 273.15, "k": v}[a]
    return {"c": k - 273.15, "f": (k - 273.15) * 9 / 5 + 32, "k": k}[b]


def fmt(x: float) -> str:
    if x == 0:
        return "0"
    if abs(x) >= 1000:
        return f"{x:,.2f}".rstrip("0").rstrip(".")
    return f"{x:.4g}"


UNIT_WORD = r"[a-z°][a-z°/]*(?: [a-z]+)?"     # 'km', 'fl oz', 'degrees c', 'nautical mile'
FORMS = [   # the phrasings a person uses; each yields (number, from-unit, to-unit)
    rf"({NUM})\s*({UNIT_WORD}?)\s+(?:to|in|into|as|->|=)\s+({UNIT_WORD})",           # 12 km to miles / 250 ml in cups
    rf"how (?:many|much) ({UNIT_WORD}) (?:is|are|in|make|equals?|per) ({NUM})\s*({UNIT_WORD})",  # how many km is 26.2 miles
    rf"({NUM})\s*({UNIT_WORD}) (?:is|equals?|=) how (?:many|much) ({UNIT_WORD})",     # 60 mph is how many km/h
    rf"({UNIT_WORD}) (?:is|are) ({NUM})\s*({UNIT_WORD})",                              # what mph is 100 kph
]


def parse(t: str):
    """(value, from_unit, to_unit) from prose, or None. Units are checked against the table so
    'how many tablespoons in half a cup' does not read 'a' as a unit."""
    t = re.sub(r"\bhalf an?\b", "0.5", re.sub(r"\ba quarter (?:of )?an?\b", "0.25", t))
    t = re.sub(r"[?.!,]+$", "", t.strip())
    for i, pat in enumerate(FORMS):
        for m in re.finditer(pat, t):
            g = m.groups()
            if i == 0:
                v, a, b = g
            elif i == 1:
                b, v, a = g
            elif i == 2:
                v, a, b = g
            else:
                b, v, a = g
            ca, cb = canon_loose(a), canon_loose(b)
            if ca and cb:
                return float(v.replace(",", ".")), ca, cb
    return None


def canon_loose(phrase: str) -> str | None:
    """Try the whole phrase, then its last word, then its last two words."""
    words = phrase.strip().split()
    for cand in (phrase, " ".join(words[-2:]), words[-1] if words else ""):
        c = canon(cand)
        if c:
            return c
    return None


def run(argument: str, app=None) -> str:
    t = argument.strip().lower().replace("°", " °").replace("  ", " ")
    got = parse(t)
    if not got:
        m = re.search(rf"({NUM})\s*({UNIT_WORD})\s+(?:to|in|into|as)\s+({UNIT_WORD})", re.sub(r"[?.!]+$", "", t))
        if m:
            bad = m.group(2) if canon_loose(m.group(2)) is None else m.group(3)
            return f"NO_MATCH: I have no table entry for the unit '{bad.strip()}'."
        return "NO_MATCH: say it as '<number> <unit> to <unit>', e.g. 12 km to miles"
    v, a, b = got
    da, db = UNITS[a][0], UNITS[b][0]
    if da != db:
        return f"NO_MATCH: {a} is {da} and {b} is {db}; they do not convert."
    out = temp(v, a, b) if da == "temp" else v * UNITS[a][1] / UNITS[b][1]
    return f"{fmt(v)} {a} = {fmt(out)} {b}"

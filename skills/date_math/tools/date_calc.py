"""Date arithmetic: days between two dates, a date plus/minus N days or weeks, the weekday of a
date, days until a date from today. ISO dates (2026-09-20) or 'Sep 20 2026' / '20 September 2026'.
Pure calendar arithmetic; the only thing it looks up is today's date on the machine clock."""

from __future__ import annotations

import datetime as dt
import re

DESCRIPTION = "date arithmetic: days between two dates, a date plus N days, the weekday of a date, days until a date"
NEEDS_ACT = False
TRIGGER = (r"(?<![\w/\\.-])\d{4}-\d{2}-\d{2}(?![\w/\\-]|\.\w)|"        # an ISO date that is not part of a path or filename
           r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?,? ?\d{1,2}(st|nd|rd|th)?,? \d{4}|"
           r"\b\d{1,2}(st|nd|rd|th)? (jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{4}|"
           r"\bdays? (between|until|till|since|from|after|before|ago)\b|\b(weekday|day of the week|what day)\b|"
           r"\bnext (mon|tues|wednes|thurs|fri|satur|sun)day")

MONTHS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
DATE_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2})"
    r"|(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]{3,9})\.?,?\s+(\d{4})"
    r"|([a-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})"
    r"|(\d{1,2})/(\d{1,2})/(\d{4})", re.I)


def parse_dates(text: str) -> list[dt.date]:
    out = []
    for m in DATE_RE.finditer(text):
        try:
            if m.group(1):
                out.append(dt.date.fromisoformat(m.group(1)))
            elif m.group(2):
                out.append(dt.date(int(m.group(4)), MONTHS[m.group(3)[:3].lower()], int(m.group(2))))
            elif m.group(5):
                out.append(dt.date(int(m.group(7)), MONTHS[m.group(5)[:3].lower()], int(m.group(6))))
            else:  # US m/d/yyyy
                out.append(dt.date(int(m.group(10)), int(m.group(8)), int(m.group(9))))
        except (KeyError, ValueError):
            continue
    return out


def today() -> dt.date:
    return dt.date.today()


def run(argument: str, app=None) -> str:
    t = argument.strip()
    low = t.lower()
    dates = parse_dates(t)
    if "today" in low or "now" in low:
        dates = dates + [today()]
    if re.search(r"\b(weekday|day of the week|what day)\b", low) and dates:
        d = dates[0]
        return f"{d.isoformat()} is a {d.strftime('%A')}"
    m = re.search(r"(plus|\+|add|minus|-|subtract|ago|before|after|from)\s*(\d+)\s*(day|week|month|year)s?", low) or \
        re.search(r"(\d+)\s*(day|week|month|year)s?\s*(from|after|before|ago)", low)
    if m and dates:
        if m.group(1).isdigit():
            n, unit, op = int(m.group(1)), m.group(2), m.group(3)
        else:
            op, n, unit = m.group(1), int(m.group(2)), m.group(3)
        sign = -1 if op in ("minus", "-", "subtract", "ago", "before") else 1
        base = dates[0]
        if unit in ("day", "week"):
            r = base + dt.timedelta(days=sign * n * (7 if unit == "week" else 1))
        else:
            months = sign * n * (12 if unit == "year" else 1)
            y, mo = divmod(base.month - 1 + months, 12)
            y += base.year
            import calendar
            day = min(base.day, calendar.monthrange(y, mo + 1)[1])
            r = dt.date(y, mo + 1, day)
        return f"{base.isoformat()} {'+' if sign > 0 else '-'} {n} {unit}{'s' if n != 1 else ''} = {r.isoformat()} ({r.strftime('%A')})"
    if len(dates) >= 2:
        a, b = dates[0], dates[1]
        n = (b - a).days
        return f"from {a.isoformat()} to {b.isoformat()} is {abs(n)} days ({abs(n) // 7} weeks and {abs(n) % 7} days){' — the second date is earlier' if n < 0 else ''}"
    if len(dates) == 1 and re.search(r"\b(until|till|to|since|left|ago|how many days)\b", low):
        d, now = dates[0], today()
        n = (d - now).days
        if n >= 0:
            return f"{n} days from today ({now.isoformat()}) until {d.isoformat()}"
        return f"{d.isoformat()} was {-n} days before today ({now.isoformat()})"
    if len(dates) == 1:
        d = dates[0]
        return f"{d.isoformat()} is a {d.strftime('%A')}, day {d.timetuple().tm_yday} of {d.year}"
    return "NO_MATCH: I need one or two dates like 2026-09-20 or 'Sep 20 2026', and what to do with them (days between, plus N days, weekday, days until)."

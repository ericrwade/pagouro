---
name: date_math
description: date arithmetic - days between two dates, a date plus or minus N days/weeks/months, the weekday of a date, days until a date
license: CC0-1.0
author: Pagouro project (first-party)
ported_by: session, 2026-09-20
source: written for Pagouro; proleptic Gregorian calendar via Python's datetime
---

# Date arithmetic

One tool, `date_calc`. It parses up to two dates (ISO `2026-09-20`, `Sep 20 2026`, `20 September
2026`, or US `9/20/2026`) and one operation. "Today" and "now" are read from the machine clock and
the answer says which date it took as today, so a wrong clock shows up in the answer rather than
hiding in it.

Not handled, on purpose: time zones, business days, holidays, and relative phrases without a
number ("next Tuesday"). A `NO_MATCH` line comes back for those; nothing is guessed.

---
name: unit_convert
description: convert a quantity between units of length, mass, volume, data, time, speed or temperature
license: CC0-1.0
author: Pagouro project (first-party)
ported_by: session, 2026-09-20
source: written for Pagouro; factors from the SI definitions and the US customary units as defined in NIST SP 811
---

# Unit conversion

One tool, `convert`, that takes `<number> <unit> to <unit>` and answers from a table. It does
no reasoning: an unknown unit, or two units of different dimensions, gets a `NO_MATCH` line and
nothing else. The reference pack `packs/units.txt` carries the same table as prose so
`pack_search` can find "how many millilitres in a cup" without calling the tool.

What was dropped in the port: nothing — this skill was written decomposed. A prose skill for a
large model would also handle currency (needs the network) and cooking-weight conversions that
depend on the ingredient; those are out of scope here (see `recipe_scale` for the latter).

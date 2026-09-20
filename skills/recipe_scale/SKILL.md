---
name: recipe_scale
description: scale a recipe's ingredient quantities up or down (double, halve, 1.5x, for 6 instead of 4)
license: CC0-1.0
author: Pagouro project (first-party)
ported_by: session, 2026-09-20
source: written for Pagouro; pairs with the Armed Forces Recipe Service pack (public domain, US Army TM 10-412)
---

# Recipe scaling

One tool, `scale_recipe`. Give it a factor and an ingredient list; it multiplies the first
quantity on each line and prints the list back with kitchen fractions (1 1/2, 3/4). It does not
convert units, does not know that eggs come whole (it will print 4 1/2 eggs and let you round),
and does not adjust cooking times — none of those are arithmetic, and a small model should not
be asked to fake them. A line with no number is returned unchanged and marked.

The reference pack `packs/kitchen_scaling.txt` holds the two or three facts a cook needs when
scaling: what does not scale linearly, and the common cup-to-gram weights for flour, sugar and
butter (approximate, and said so).

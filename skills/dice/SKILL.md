---
name: dice
description: roll dice, flip a coin, pick a random number or item - genuinely random, from the OS entropy pool, with the provenance shown
license: CC0-1.0
author: Pagouro project (first-party)
ported_by: session, 2026-09-20 (Eric's ask: "a local and completely honest dice roller")
source: written for Pagouro; os.urandom + rejection sampling
---

# Dice — honest randomness

A language model cannot roll a die. Asked for a d20 it emits a plausible number that is not
random: the distribution is skewed, and a "second roll" is correlated with the first. That is the
bluff pattern in its purest form, so this skill is the harness doing what the model cannot: the
tool draws bytes from the operating system's entropy pool (`os.urandom`, the same source
cryptography uses), reduces them to the requested range by rejection sampling (no modulo bias),
and returns the result **with its provenance** — the bytes used and their hash — so a sceptic can
see the number was not invented.

`seed <word>` makes a reproducible sequence for games and is labelled "SEEDED (not random)".

Why not mouse or finger movement for entropy? On any current operating system the entropy pool
already mixes hardware randomness; a slider adds ceremony, not randomness. The honest claim is
"from the OS, not from the model", and that is what the tool prints.

Forms: `d20`, `2d6+3`, `3d8`, `flip a coin`, `a number between 1 and 100`, `pick one: a, b, c`,
`shuffle: a, b, c, d`. Limits: 1–100 dice of 2–1000 sides. Anything else: `NO_MATCH`.

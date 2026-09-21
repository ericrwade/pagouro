"""Honest randomness. A language model cannot roll a die: it emits a plausible number that is not
random. This tool draws from the operating system's entropy pool (os.urandom, the same source
cryptography uses), reduces the bytes to the requested range by rejection sampling (no modulo
bias), and reports the provenance with the result so the number can be believed for what it is.

Forms: "d20", "roll 2d6+3", "3d8", "flip a coin", "a number between 1 and 100", "pick one:
tea, coffee, water", "shuffle: a, b, c, d". Add "seed 1234" for a reproducible (NOT random)
sequence for games — it is labelled as such."""

from __future__ import annotations

import hashlib
import os
import random
import re

DESCRIPTION = "roll dice, flip a coin, pick a random number or item — genuinely random from the OS entropy pool, provenance shown"
NEEDS_ACT = False
TRIGGER = (r"\b(roll|rolls|rolling|dice|die|d[1-9]\d{0,2}\b|\d+d\d+|flip a coin|coin flip|heads or tails|"
           r"random number|number between|pick (?:one|a random)|choose (?:one|randomly|at random)|shuffle)\b")


class OSRandom:
    """Uniform integers from os.urandom by rejection sampling; keeps the raw bytes it used."""
    def __init__(self):
        self.used = bytearray()

    def below(self, n: int) -> int:
        if n <= 1:
            return 0
        nbytes = (n.bit_length() + 7) // 8
        limit = (256 ** nbytes // n) * n          # largest multiple of n that fits: reject above it
        while True:
            b = os.urandom(nbytes)
            self.used += b
            v = int.from_bytes(b, "big")
            if v < limit:
                return v % n


def run(argument: str, app=None) -> str:
    t = argument.strip().lower()
    seed_m = re.search(r"\bseed\s+(\w+)", t)
    if seed_m:
        rng = random.Random(seed_m.group(1)); source = f"SEEDED (not random): seed '{seed_m.group(1)}', Python's Mersenne Twister; the same seed always gives the same result"
        below = lambda n: rng.randrange(n)
        used = None
    else:
        osr = OSRandom(); source = "OS entropy pool (os.urandom), rejection sampling, no modulo bias"
        below = osr.below
        used = osr.used
    out = []
    # coin
    if re.search(r"coin|heads or tails", t):
        out.append("coin: " + ("HEADS" if below(2) == 0 else "TAILS"))
    # dice: NdS(+M)
    for m in re.finditer(r"(?<![a-z0-9])(\d*)d(\d{1,3})(?![a-z0-9])\s*([+-]\s*\d+)?", t):   # a real NdS token: not 'and 100', not 'seed 42'
        n = int(m.group(1)) if m.group(1) else 1
        sides = int(m.group(2))
        mod = int(re.sub(r"\s", "", m.group(3))) if m.group(3) else 0
        if not (1 <= n <= 100 and 2 <= sides <= 1000):
            out.append(f"NO_MATCH: {n}d{sides} is outside 1-100 dice of 2-1000 sides."); continue
        rolls = [below(sides) + 1 for _ in range(n)]
        total = sum(rolls) + mod
        out.append(f"{n}d{sides}{'%+d' % mod if mod else ''}: {' + '.join(map(str, rolls))}" + (f" {'%+d' % mod}" if mod else "") + f" = {total}" if n > 1 or mod else f"d{sides}: {rolls[0]}")
    # range
    m = re.search(r"between\s+(-?\d+)\s+and\s+(-?\d+)", t)
    if m:
        lo, hi = sorted((int(m.group(1)), int(m.group(2))))
        out.append(f"number in [{lo}, {hi}]: {lo + below(hi - lo + 1)}")
    # pick / shuffle
    m = re.search(r"(?:pick (?:one|a random)|choose (?:one|randomly|at random)|shuffle)\s*(?:of|from|between)?\s*:?\s*(.+)$", t)
    if m:
        items = [x.strip() for x in re.split(r",|;|\bor\b|\band\b", m.group(1)) if x.strip()]
        if len(items) >= 2:
            if "shuffle" in t:
                order = items[:]
                for i in range(len(order) - 1, 0, -1):
                    j = below(i + 1); order[i], order[j] = order[j], order[i]
                out.append("shuffled: " + ", ".join(order))
            else:
                out.append("picked: " + items[below(len(items))])
    if not out:
        return "NO_MATCH: say 'd20', '2d6+3', 'flip a coin', 'a number between 1 and 100', 'pick one: a, b, c' or 'shuffle: a, b, c'."
    prov = f"source: {source}"
    if used is not None:
        prov += f"; bytes used: {used.hex() or '-'}; sha256 of bytes: {hashlib.sha256(bytes(used)).hexdigest()[:16]}"
    return "\n".join(out) + "\n" + prov

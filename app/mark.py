"""The Pagouro mark, procedural, in the HOUSE palette (D-74, Belle Époque). Standard library only.

Not a creature drawn from parts (that was artkit.hermit_crab, the placeholder) but a poster
object: a round cream medallion with a Chéret sunburst, the hermit crab as one flat silhouette
with a single heavy warm-black contour, Art Nouveau whiplash antennae, a spiral shell in the
gold-ochre ramp, and a lettered band. 64 px. Deterministic per seed: colourway, sunburst, band,
shell tilt. Everything is quantised to the palette on the way out, so the mark is by construction
inside the 32 colours the manifest lists.

    python app/mark.py            -> docs/samples/palettes/marks.png (a sheet of 12)
"""

from __future__ import annotations

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artkit  # noqa: E402
from palettes import CANDIDATES, HOUSE  # noqa: E402

Pixel = tuple[int, int, int]
T: Pixel = (0, 0, 0)

# 3x5 pixel glyphs for the band (1 = ink)
GLYPHS = {
    "P": ["111", "101", "111", "100", "100"], "A": ["010", "101", "111", "101", "101"],
    "G": ["111", "100", "101", "101", "111"], "O": ["111", "101", "101", "101", "111"],
    "U": ["101", "101", "101", "101", "111"], "R": ["111", "101", "111", "110", "101"],
}


def disc(img, cx, cy, r, col, only_on=None):
    n = len(img)
    for y in range(max(0, int(cy - r - 1)), min(n, int(cy + r + 2))):
        for x in range(max(0, int(cx - r - 1)), min(n, int(cx + r + 2))):
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r and (only_on is None or img[y][x] == only_on):
                img[y][x] = col


def ellipse(img, cx, cy, rx, ry, col, only_on=None):
    n = len(img)
    for y in range(n):
        for x in range(n):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1 and (only_on is None or img[y][x] == only_on):
                img[y][x] = col


def stroke(img, pts, col, w=1):
    for (x, y) in pts:
        disc(img, x, y, w / 2.0 + 0.3, col)


def bezier(p0, p1, p2, steps=60):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / steps for i in range(steps + 1))]


def outline(img, mask_of, ink, width=2):
    """Heavy contour: every pixel of `mask_of` colours that touches something else gets ink, `width` deep."""
    n = len(img)
    for _ in range(width):
        edge = []
        for y in range(n):
            for x in range(n):
                if img[y][x] in mask_of:
                    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        yy, xx = y + dy, x + dx
                        if not (0 <= yy < n and 0 <= xx < n) or img[yy][xx] not in mask_of and img[yy][xx] != ink:
                            edge.append((y, x)); break
        for y, x in edge:
            img[y][x] = ink


def letters(img, text, x0, y0, col, scale=1):
    x = x0
    for ch in text:
        g = GLYPHS.get(ch)
        if not g:
            x += 2 * scale; continue
        for gy, row in enumerate(g):
            for gx, bit in enumerate(row):
                if bit == "1":
                    for sy in range(scale):
                        for sx in range(scale):
                            yy, xx = y0 + gy * scale + sy, x + gx * scale + sx
                            if 0 <= yy < len(img) and 0 <= xx < len(img):
                                img[yy][xx] = col
        x += 4 * scale


def mark(seed: int = 0, n: int = 64, band: bool = True) -> list[list[Pixel]]:
    rng = random.Random(seed)
    pal = CANDIDATES[HOUSE]
    R = pal.ramps
    ink, paper = pal.ink, R["poster"][3]
    ways = [("vermilion", "goldochre", "chrome"), ("prussian", "chrome", "vermilion"), ("vermilion", "prussian", "goldochre"),
            ("dustyrose", "sage", "goldochre"), ("goldochre", "prussian", "vermilion"), ("sage", "vermilion", "chrome")]
    crab_r, shell_r, ray_r = ways[seed % len(ways)]
    img = [[T] * n for _ in range(n)]
    c = n / 2.0
    # medallion: cream disc with a sunburst of pale rays, thin ring in the ray colour, heavy outer contour
    disc(img, c, c, n * 0.47, paper)
    if seed % 3 != 2:
        rays = 12 + 2 * (seed % 3)
        for y in range(n):
            for x in range(n):
                if img[y][x] == paper:
                    a = math.atan2(y + 0.5 - c, x + 0.5 - c)
                    d = math.hypot(x + 0.5 - c, y + 0.5 - c)
                    if int((a + math.pi) / (2 * math.pi) * rays) % 2 == 0 and d > n * 0.13:
                        img[y][x] = R["poster"][2]
    disc(img, c, c, n * 0.47, R[ray_r][2], only_on=None) if False else None
    # ring
    for y in range(n):
        for x in range(n):
            d = math.hypot(x + 0.5 - c, y + 0.5 - c)
            if n * 0.43 <= d <= n * 0.47:
                img[y][x] = R[ray_r][1]
    # THE FIGURE (Eric, 2026-09-20): the crab retreated into its shell — the shell is the mass, the
    # crab is only what shows at the mouth: two folded claws under the lip, eyes on short stalks
    # peeking over them, thin antennae. No body. Seen from the front-left, shell high and behind.
    shell = R[shell_r]
    body = R[crab_r][2]
    sx, sy = c + n * 0.08, c - n * 0.07          # shell centre, right and high
    srx, sry = n * 0.30, n * 0.25                # a fat ellipse, the apex up-right
    ellipse(img, sx, sy, srx, sry, shell[2])
    ellipse(img, sx + n * 0.05, sy - n * 0.05, srx * 0.62, sry * 0.6, shell[3], only_on=shell[2])   # highlight plane
    # growth lines: three arcs following the shell, in the dark shell tone (the poster's two-tone shading)
    for k, f in enumerate((0.92, 0.72, 0.52)):
        for i in range(0, 360, 2):
            a = math.radians(i)
            x, y = sx + n * 0.03 + srx * f * math.cos(a) * 0.98, sy - n * 0.03 + sry * f * math.sin(a)
            if -1.3 < a - math.pi * 0.85 < 1.6 and 0 <= int(x) < n and 0 <= int(y) < n and img[int(y)][int(x)] in (shell[2], shell[3]):
                img[int(y)][int(x)] = shell[1]
    # the aperture: a dark opening low-left of the shell, where the crab lives
    ax, ay = sx - srx * 0.58, sy + sry * 0.50
    ellipse(img, ax, ay, n * 0.19, n * 0.12, shell[0])
    # claws: two knuckled lobes folded under the lip, filling the opening; the big one forward-left
    cx1, cy1 = ax - n * 0.04, ay + n * 0.03
    disc(img, cx1, cy1, n * 0.10, body)
    outline(img, {body}, ink, width=1)
    disc(img, cx1 + n * 0.14, cy1 + n * 0.03, n * 0.08, body)
    # knuckle lines and the pincer notch
    for (ox, oy, rr) in ((cx1, cy1, n * 0.10), (cx1 + n * 0.14, cy1 + n * 0.03, n * 0.08)):
        for k in range(int(rr * 0.8)):
            x, y = int(ox - rr * 0.2 + k * 0.6), int(oy - rr + k * 0.9)
            if 0 <= x < n and 0 <= y < n and img[y][x] == body:
                img[y][x] = R[crab_r][1]
        for k in range(int(rr * 0.7)):                       # pincer gap on the outer edge
            x, y = int(ox - rr + k), int(oy + rr * 0.35)
            if 0 <= x < n and 0 <= y < n and img[y][x] == body:
                img[y][x] = shell[0]
    # eyes: two short stalks rising from between the claws and the lip, big dark eyes on top
    for k, ex in enumerate((cx1 + n * 0.01, cx1 + n * 0.11)):
        ey = ay - n * 0.09
        stroke(img, [(ex, ey + j * 0.5) for j in range(int(n * 0.16))], body, 1.8)
        disc(img, ex, ey - n * 0.01, n * 0.042, ink)
        disc(img, ex, ey - n * 0.01, n * 0.030, R["poster"][3])
        disc(img, ex + n * 0.005, ey, n * 0.017, ink)
    # antennae: the one whiplash line, out to the left and up
    for k, sign in enumerate((1.0, 0.7)):
        p0 = (cx1 - n * 0.02, ay - n * 0.02 - k * n * 0.03)
        p1 = (cx1 - n * 0.16, ay - n * 0.14 * sign)
        p2 = (cx1 - n * 0.30, ay - n * 0.02 - k * n * 0.06)
        stroke(img, bezier(p0, p1, p2), R[crab_r][1], 1.1)
    # single heavy contour around the whole figure (shell + claws + stalks), in ink
    outline(img, {shell[0], shell[1], shell[2], shell[3], body, R[crab_r][1]}, ink, width=2 if n >= 64 else 1)
    # band with lettering
    if band:
        y0 = int(c + n * 0.26)
        for y in range(y0, y0 + 9 if n >= 64 else y0 + 7):
            for x in range(int(c - n * 0.36), int(c + n * 0.36)):
                if 0 <= y < n and 0 <= x < n:
                    img[y][x] = R[crab_r][1] if crab_r != "goldochre" else R["prussian"][1]
        letters(img, "PAGOURO", int(c - 13), y0 + 2, paper)
    # outer contour of the medallion
    for y in range(n):
        for x in range(n):
            d = math.hypot(x + 0.5 - c, y + 0.5 - c)
            if n * 0.455 <= d <= n * 0.475:
                img[y][x] = ink
    return pal.quantize(img, transparent=T)


def sheet(seeds=range(12), n=64, scale=4, path=None) -> str:
    pal = CANDIDATES[HOUSE]
    cols = 6
    rows = (len(seeds) + cols - 1) // cols
    W, H = cols * (n + 6) + 6, rows * (n + 6) + 6
    board = [[pal.ramps["poster"][1]] * W for _ in range(H)]
    for i, s in enumerate(seeds):
        m = mark(s, n)
        ox, oy = 6 + (i % cols) * (n + 6), 6 + (i // cols) * (n + 6)
        for y, row in enumerate(m):
            for x, px in enumerate(row):
                if px != T:
                    board[oy + y][ox + x] = px
    big = [[px for px in row for _ in range(scale)] for row in board for _ in range(scale)]
    path = path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "samples", "palettes", "marks.png")
    artkit.write_png(path, big)
    return path


if __name__ == "__main__":
    print(sheet())

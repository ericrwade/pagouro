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
    # shell: spiral disc, tilted, upper right of centre
    sx, sy, sr = c + n * 0.13, c - n * 0.06, n * 0.19
    disc(img, sx, sy, sr, R[shell_r][2])
    disc(img, sx, sy, sr, R[shell_r][1], only_on=None) if False else None
    tilt = rng.uniform(-0.6, 0.6)
    for i in range(0, 700):
        a = math.radians(i) + tilt
        r = sr * (i / 700.0) ** 0.75
        x, y = int(sx + r * math.cos(a)), int(sy + r * math.sin(a))
        if 0 <= x < n and 0 <= y < n and img[y][x] == R[shell_r][2]:
            img[y][x] = R[shell_r][0]
    # crab body: one flat plane — a wide ellipse under the shell's mouth, two big claws forward-left, legs
    bx, by = c - n * 0.10, c + n * 0.09
    body = R[crab_r][2]
    ellipse(img, bx, by, n * 0.17, n * 0.10, body)
    disc(img, bx - n * 0.20, by - n * 0.04, n * 0.085, body)      # big claw
    disc(img, bx - n * 0.15, by + n * 0.10, n * 0.065, body)      # small claw
    # pincer gaps
    for (ox, oy, rr) in ((bx - n * 0.20, by - n * 0.04, n * 0.085), (bx - n * 0.15, by + n * 0.10, n * 0.065)):
        for k in range(int(rr * 0.9)):
            for dy in range(-(k // 3), k // 3 + 1):
                x, y = int(ox - rr + k), int(oy + dy)
                if 0 <= x < n and 0 <= y < n and img[y][x] == body:
                    img[y][x] = paper if img[y][x] == body else img[y][x]
    for k in range(3):                                            # legs: three strokes each side, flat
        stroke(img, [(bx - n * 0.02 - k * n * 0.06 + j * 0.3, by + n * 0.08 + j * 0.9) for j in range(int(n * 0.08))], body, 1.6)
        stroke(img, [(bx + n * 0.08 + k * n * 0.05 + j * 0.5, by + n * 0.07 + j * 0.8) for j in range(int(n * 0.07))], body, 1.6)
    # eyes on whiplash stalks (Art Nouveau curve), dots in ink
    for side in (-1, 1):
        p0 = (bx + side * n * 0.04, by - n * 0.08)
        p1 = (bx + side * n * 0.10, by - n * 0.24)
        p2 = (bx + side * n * 0.02 + (n * 0.06 if side > 0 else -n * 0.02), by - n * 0.27)
        stroke(img, bezier(p0, p1, p2), body, 1.4)
        ex, ey = p2
        disc(img, ex, ey, 1.6, ink)
    # a darker plane on the body for the poster's two-tone shadow
    ellipse(img, bx + n * 0.03, by + n * 0.03, n * 0.10, n * 0.05, R[crab_r][1], only_on=body)
    # single heavy contour around crab + shell
    outline(img, {R[crab_r][2], R[crab_r][1], R[shell_r][2], R[shell_r][0]}, ink, width=2 if n >= 64 else 1)
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

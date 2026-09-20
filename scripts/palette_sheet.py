"""Render the O-28 palette candidates as PNG sheets for Eric to choose from.

For each candidate in app/palettes.py: the 32 swatches as an 8x4 ramp grid, then six
program-drawn hermit crabs and three test sprites quantised to that palette on the palette's
own paper tone and on ink, upscaled x6. Also a combined sheet, and a README with the hex values.

    python scripts/palette_sheet.py            -> docs/samples/palettes/{tradecard,gaslight,naturalist,sheet}.png
"""

from __future__ import annotations

import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))
import artkit  # noqa: E402
from palettes import CANDIDATES, Palette  # noqa: E402

OUT = os.path.join(ROOT, "docs", "samples", "palettes")
SCALE = 6
T = (0, 0, 0)


def blank(w: int, h: int, c) -> list:
    return [[c] * w for _ in range(h)]


def paste(dst: list, src: list, x0: int, y0: int, transparent=None) -> None:
    for y, row in enumerate(src):
        for x, px in enumerate(row):
            if transparent is not None and px == transparent:
                continue
            if 0 <= y0 + y < len(dst) and 0 <= x0 + x < len(dst[0]):
                dst[y0 + y][x0 + x] = px


def upscale(img: list, k: int) -> list:
    return [[px for px in row for _ in range(k)] for row in img for _ in range(k)]


def swatch_grid(p: Palette, cell: int = 6) -> list:
    g = blank(4 * cell, 8 * cell, p.paper)
    for ri, ramp in enumerate(p.ramps.values()):
        for ci, c in enumerate(ramp):
            for y in range(cell - 1):
                for x in range(cell - 1):
                    g[ri * cell + y][ci * cell + x] = c
    return g


def crab_in(p: Palette, seed: int, n: int = 32) -> list:
    ramps = list(p.ramps.values())
    # shell from ramps 2..7 by seed, body from a different warm ramp; both then snapped to the palette
    shell = ramps[2 + seed % 6]
    body = ramps[2 + (seed + 3) % 6]
    return p.quantize(artkit.hermit_crab(seed, n, shell=shell, body=body, ink=p.ink, transparent=T), transparent=T)


def sheet_for(p: Palette) -> list:
    n = 32
    pad = 4
    crabs = [crab_in(p, s) for s in range(6)]
    blobs = [p.quantize(artkit.test_sprite(s, n, palette="ember", transparent=T), transparent=T) for s in range(3)]
    w = pad + 4 * 6 + pad + 9 * (n + pad) + pad
    h = pad + max(8 * 6, 2 * (n + pad)) + pad
    board = blank(w, h, p.paper)
    # right half of the board is ink, so each sprite shows on both grounds
    for y in range(h):
        for x in range(w // 2 + 12, w):
            board[y][x] = p.ink
    paste(board, swatch_grid(p), pad, pad)
    x = pad + 4 * 6 + pad
    for i, c in enumerate(crabs):
        paste(board, c, x + i * (n + pad), pad, transparent=T)
    for i, b in enumerate(blobs):
        paste(board, b, x + (6 + i) * (n + pad), pad, transparent=T)
    # second row: the same crabs mirrored in tone order, so the ink ground gets crabs too
    for i, c in enumerate(reversed(crabs)):
        paste(board, c, x + i * (n + pad), pad + n + pad, transparent=T)
    return board


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    sheets = []
    lines = ["# Palette candidates for Pagouro Draws (O-28)\n",
             "Rendered by `scripts/palette_sheet.py` from `app/palettes.py`. Everything on these sheets is",
             "program-drawn (the hermit crab and the blob sprites are procedural, O-18) and then snapped to the",
             "candidate's 32 colours - no model was involved. Left half of each sheet: the palette's paper tone;",
             "right half: its ink. Pick one; it becomes `HOUSE` and is listed in the release manifest.\n"]
    for key, p in CANDIDATES.items():
        board = sheet_for(p)
        big = upscale(board, SCALE)
        path = os.path.join(OUT, f"{key}.png")
        artkit.write_png(path, big)
        sheets.append(board)
        print(f"{key}: {len(big[0])}x{len(big)} -> {os.path.relpath(path, ROOT)}")
        lines.append(f"## {p.name} (`{key}`)\n\n{p.brief}\n\n![{p.name}]({key}.png)\n")
        for rname, ramp in p.as_dict()["ramps"].items():
            lines.append(f"- {rname}: " + " ".join(f"`{c}`" for c in ramp))
        lines.append("")
    gap = 6
    w = max(len(b[0]) for b in sheets)
    h = sum(len(b) for b in sheets) + gap * (len(sheets) - 1)
    combined = blank(w, h, (255, 255, 255))
    y = 0
    for b in sheets:
        paste(combined, b, 0, y)
        y += len(b) + gap
    artkit.write_png(os.path.join(OUT, "sheet.png"), upscale(combined, SCALE))
    io.open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    io.open(os.path.join(OUT, "candidates.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps({k: p.as_dict() for k, p in CANDIDATES.items()}, indent=1) + "\n")
    print("sheet.png, README.md, candidates.json written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Pixel-art plumbing for the stick (O-21, docs/IMAGE_MVP.md). Standard library only.

An image here is a list of rows, each a list of (r, g, b) tuples, 0-255. Three things:

  render_ansi(img)      -> str   the image as terminal text: Unicode half-blocks (two pixels per
                                 character cell) with 24-bit ANSI colour, so a 32x32 sprite is
                                 16 rows x 32 columns in Windows Terminal / conhost.
  write_png(path, img)          a real PNG (zlib + struct; no Pillow), for `/act` mode.
  read_png(path)        -> img  8-bit RGB/RGBA non-interlaced PNGs only (enough for our own files).
  test_sprite(seed, n)  -> img  a program-generated 16x16..64x64 sprite: symmetric, palette-
                                quantised, so the render path can be shown before any model
                                exists. Labelled synthetic by construction (O-18).

The drawing MODEL is not here yet; this file is the frame it plugs into.
"""

from __future__ import annotations

import random
import struct
import zlib

Pixel = tuple[int, int, int]
Image = list[list[Pixel]]

RESET = "\x1b[0m"


def render_ansi(img: Image, transparent: Pixel | None = None) -> str:
    """Two vertical pixels per cell: foreground = top pixel on '▀', background = bottom pixel."""
    rows = []
    h = len(img)
    for y in range(0, h, 2):
        top = img[y]
        bot = img[y + 1] if y + 1 < h else [transparent or (0, 0, 0)] * len(top)
        cells = []
        for t, b in zip(top, bot):
            if transparent is not None and t == transparent and b == transparent:
                cells.append(RESET + " ")
            elif transparent is not None and b == transparent:
                cells.append(f"\x1b[0m\x1b[38;2;{t[0]};{t[1]};{t[2]}m▀")
            elif transparent is not None and t == transparent:
                cells.append(f"\x1b[0m\x1b[38;2;{b[0]};{b[1]};{b[2]}m▄")
            else:
                cells.append(f"\x1b[38;2;{t[0]};{t[1]};{t[2]}m\x1b[48;2;{b[0]};{b[1]};{b[2]}m▀")
        rows.append("".join(cells) + RESET)
    return "\n".join(rows)


def render_ascii(img: Image) -> str:
    """Fallback for consoles without colour: luminance ramp, one char per pixel, doubled width."""
    ramp = " .:-=+*#%@"
    out = []
    for row in img:
        out.append("".join(ramp[min(9, int((0.299 * r + 0.587 * g + 0.114 * b) / 25.6))] * 2 for r, g, b in row))
    return "\n".join(out)


def write_png(path: str, img: Image) -> int:
    """Minimal PNG encoder (8-bit RGB, filter 0). Returns bytes written."""
    h, w = len(img), len(img[0])
    raw = b"".join(b"\x00" + bytes(c for px in row for c in px) for row in img)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def read_png(path: str) -> Image:
    """Decode our own PNGs (and most 8-bit RGB/RGBA non-interlaced ones)."""
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos, idat, w = 8, b"", 0
    while pos < len(data):
        ln, tag = struct.unpack(">I", data[pos:pos + 4])[0], data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if tag == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", body)
            assert depth == 8 and ctype in (2, 6) and inter == 0, "only 8-bit RGB/RGBA, non-interlaced"
            bpp = 3 if ctype == 2 else 4
        elif tag == b"IDAT":
            idat += body
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * bpp
    img, prev = [], bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1: line[i] = (line[i] + a) & 255
            elif f == 2: line[i] = (line[i] + b) & 255
            elif f == 3: line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        img.append([(line[i], line[i + 1], line[i + 2]) for i in range(0, stride, bpp)])
        prev = line
    return img


PALETTES = {
    "gameboy": [(15, 56, 15), (48, 98, 48), (139, 172, 15), (155, 188, 15)],
    "ember": [(20, 12, 28), (68, 36, 52), (150, 60, 60), (208, 120, 70), (240, 200, 120), (250, 240, 200)],
    "sea": [(10, 20, 40), (20, 60, 100), (40, 120, 160), (90, 190, 200), (200, 240, 240)],
    "moss": [(24, 20, 16), (60, 70, 30), (100, 130, 50), (170, 190, 90), (230, 235, 180)],
}


def test_sprite(seed: int = 0, n: int = 32, palette: str = "ember", transparent: Pixel = (0, 0, 0)) -> Image:
    """A mirrored blob creature with an outline, in a fixed palette. Deterministic per seed."""
    rng = random.Random(seed)
    pal = PALETTES.get(palette, PALETTES["ember"])
    half = n // 2
    mask = [[False] * n for _ in range(n)]
    # random walk fills on the left half, mirrored to the right
    for _ in range(n * n // 3):
        x, y = rng.randrange(half // 3, half), rng.randrange(n // 5, n - n // 5)
        for _ in range(rng.randrange(3, n // 2)):
            mask[y][x] = True
            x = min(half - 1, max(0, x + rng.choice((-1, 0, 1))))
            y = min(n - 2, max(1, y + rng.choice((-1, 0, 1))))
    for y in range(n):
        for x in range(half):
            mask[y][n - 1 - x] = mask[y][x]
    img: Image = [[transparent] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            if not mask[y][x]:
                continue
            edge = any(not (0 <= y + dy < n and 0 <= x + dx < n and mask[y + dy][x + dx])
                       for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)))
            shade = 0 if edge else 1 + min(len(pal) - 2, (y * (len(pal) - 1)) // n + rng.choice((0, 0, 1)))
            img[y][x] = pal[shade]
    # eyes: two darkest-palette pixels, mirrored
    ey, ex = n // 3, half - max(2, half // 4)
    if mask[ey][ex]:
        img[ey][ex] = pal[0]; img[ey][n - 1 - ex] = pal[0]
    return img

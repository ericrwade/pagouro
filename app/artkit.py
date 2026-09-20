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


def hermit_crab(seed: int = 0, n: int = 32, shell: list[Pixel] | None = None, body: list[Pixel] | None = None,
                ink: Pixel = (20, 16, 14), transparent: Pixel = (0, 0, 0)) -> Image:
    """A program-drawn hermit crab (spiral shell, body, two claws, eye stalks), deterministic per
    seed: shell tilt, spiral tightness and claw size vary. Synthetic by construction (O-18) - this is
    the subject stand-in for palette sheets and the /art demo until the drawing model exists."""
    import math
    rng = random.Random(seed)
    shell = shell or PALETTES["ember"][1:5]
    body = body or PALETTES["ember"][2:6]
    img: Image = [[transparent] * n for _ in range(n)]
    s = n / 32.0
    cx, cy, R = int(19 * s), int(14 * s), 9 * s * rng.uniform(0.9, 1.05)       # shell centre and radius
    tilt = rng.uniform(-0.5, 0.5)
    turns = rng.uniform(1.6, 2.4)
    # shell disc, shaded by height, then the spiral groove in the darker shell tone
    for y in range(n):
        for x in range(n):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            if dx * dx + dy * dy <= R * R:
                t = (dy + R) / (2 * R)
                img[y][x] = shell[min(len(shell) - 1, 1 + int(t * (len(shell) - 1)))]
    for i in range(int(360 * turns)):
        a = math.radians(i) + tilt
        r = R * (i / (360.0 * turns)) ** 0.8
        x, y = int(cx + r * math.cos(a)), int(cy + r * math.sin(a))
        if 0 <= x < n and 0 <= y < n and img[y][x] != transparent:
            img[y][x] = shell[0]
    # body: a blob emerging from the shell's lower-left, drawn as overlapping discs
    bx, by = cx - R * 0.9, cy + R * 0.35
    discs = [(bx, by, 4.2 * s), (bx - 3 * s, by + 1.5 * s, 3.4 * s)]
    claw = rng.uniform(3.0, 4.2) * s
    claws = [(bx - 8.5 * s, by - 1.5 * s, claw), (bx - 6.5 * s, by + 5.0 * s, claw * 0.75)]  # big claw up front, small below
    for (ox, oy, rr) in discs + claws:
        for y in range(n):
            for x in range(n):
                dx, dy = x + 0.5 - ox, y + 0.5 - oy
                if dx * dx + dy * dy <= rr * rr and img[y][x] == transparent:
                    t = (dy + rr) / (2 * rr)
                    img[y][x] = body[min(len(body) - 1, 1 + int(t * (len(body) - 1)))]
    # pincer: a V-shaped gap cut out of each claw's leading edge
    for (ox, oy, rr) in claws:
        for k in range(int(rr * 0.9)):
            for dy in range(-(k // 2) - 0, k // 2 + 1):
                x, y = int(ox - rr + k), int(oy + dy)
                if 0 <= x < n and 0 <= y < n:
                    img[y][x] = transparent
    # legs: three jointed strokes walking out from under the body
    for k in range(3):
        lx = int(bx - 1 * s - k * 3 * s)
        for j in range(int(5 * s)):
            x, y = lx - j // 2, int(by + 3 * s + j)
            if 0 <= x < n and 0 <= y < n and img[y][x] == transparent:
                img[y][x] = body[1] if j < 3 * s else body[0]
    # eye stalks: two verticals rising from the body's top, 2-px ink eyes
    for ex in (int(bx - 1.5 * s), int(bx + 1.5 * s)):
        for j in range(int(6 * s)):
            y = int(by - 3 * s - j)
            if 0 <= ex < n and 0 <= y < n:
                img[y][ex] = body[2]
        for j in range(2):
            y = int(by - 9 * s) + j
            if 0 <= ex < n and 0 <= y < n:
                img[y][ex] = ink
    # one-pixel outline in ink (the house rule): every filled pixel touching transparent
    out = [row[:] for row in img]
    for y in range(n):
        for x in range(n):
            if img[y][x] == transparent:
                continue
            if any(not (0 <= y + dy < n and 0 <= x + dx < n) or img[y + dy][x + dx] == transparent
                   for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                out[y][x] = ink
    return out

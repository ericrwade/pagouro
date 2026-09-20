"""Slice the Kenney packs that ship only sprite sheets (D-67). Needs Pillow (the project venv).

Kenney's roguelike / 1-bit sheets are 16 px tiles with a 1 px gutter: width = n*17 or n*17-1.
For each pack zip in data/images/kenney/ the `_transparent` (or `tileset_*`) sheets are cut on
that grid, fully transparent tiles are dropped, and each tile becomes a PNG under the pack folder
with a row in the pack's index.jsonl (sheet path, grid position, sha256). The pack's ledger row
is updated with the new n_images and a `sliced` note. Re-runnable: already-sliced sheets are skipped.

    .venv/Scripts/python.exe scripts/slice_kenney_sheets.py [--tile 16 --gutter 1]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEN = os.path.join(ROOT, "data", "images", "kenney")


def grid_fits(w: int, h: int, tile: int, gutter: int) -> bool:
    step = tile + gutter
    ok = lambda x: (x + gutter) % step == 0 or x % step == 0     # with or without a trailing gutter
    return ok(w) and ok(h)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tile", type=int, default=16)
    ap.add_argument("--gutter", type=int, default=1)
    a = ap.parse_args()
    from PIL import Image
    led_path = os.path.join(KEN, "ledger.jsonl")
    rows = [json.loads(l) for l in io.open(led_path, encoding="utf-8") if l.strip()]
    total = 0
    for r in rows:
        slug = r["slug"]
        zpath = os.path.join(KEN, f"{slug}.zip")
        if not os.path.exists(zpath):
            continue
        pack_dir = os.path.join(KEN, slug)
        idx_path = os.path.join(pack_dir, "index.jsonl")
        done_sheets = set()
        if os.path.exists(idx_path):
            for l in io.open(idx_path, encoding="utf-8"):
                if l.strip():
                    done_sheets.add(json.loads(l).get("sheet"))
        n = 0
        with zipfile.ZipFile(zpath) as z, io.open(idx_path, "a", encoding="utf-8", newline="\n") as idx:
            for info in z.infolist():
                name = info.filename
                low = name.lower()
                if not low.endswith(".png") or name in done_sheets:
                    continue
                if not (("_transparent" in low) or ("-transparent" in low)) or "packed" in low:
                    continue                      # the transparent, gutter-spaced sheet only (packed = same tiles, no gutter)
                if any(k in low for k in ("preview", "sample")):
                    continue
                im = Image.open(io.BytesIO(z.read(info))).convert("RGBA")
                w, h = im.size
                if not grid_fits(w, h, a.tile, a.gutter):
                    print(f"  {slug}: {name} {w}x{h} does not fit a {a.tile}+{a.gutter} grid; skipped")
                    continue
                step = a.tile + a.gutter
                cols, rws = (w + a.gutter) // step, (h + a.gutter) // step
                base = re.sub(r"[^A-Za-z0-9_\-]+", "_", os.path.splitext(os.path.basename(name))[0])
                for ry in range(rws):
                    for cx in range(cols):
                        t = im.crop((cx * step, ry * step, cx * step + a.tile, ry * step + a.tile))
                        if not t.getbbox() or t.getchannel("A").getextrema()[1] == 0:
                            continue
                        p = os.path.join(pack_dir, f"{base}_r{ry:02d}_c{cx:02d}.png")
                        t.save(p, "PNG", optimize=True)
                        b = open(p, "rb").read()
                        idx.write(json.dumps({"file": os.path.relpath(p, ROOT).replace("\\", "/"), "sheet": name,
                                              "row": ry, "col": cx, "width": a.tile, "height": a.tile,
                                              "sha256": hashlib.sha256(b).hexdigest()}) + "\n")
                        n += 1
        if n:
            r["n_images"] = r.get("n_images", 0) + n
            r["sliced"] = f"{n} tiles cut from sheets on a {a.tile}px grid with {a.gutter}px gutters"
            total += n
            print(f"  {slug}: +{n} tiles from sheets")
    with io.open(led_path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"done: {total:,} tiles sliced; Kenney total {sum(r.get('n_images', 0) for r in rows):,} images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""The on-stick drawing model's training set (D-67, D-74): every image we own the rights to, at 32 and
64 px, quantised to the HOUSE palette, in one folder with one ledger. Needs Pillow (project venv).

Sources and what each is for:
  * Kenney sprites/tiles (CC0, ~9,700)          — volume; the vocabulary of small readable shapes
  * Met curated prints (CC0, ~350)              — the style: the print world at 64 px
  * LoC Artists Posters (public domain, 1,411)  — the style again, the poster world at 64 px
  * LoRA candidates (D-75, CC0 outputs, 192)    — the subject: hermit-crab marks in the house look
  * the procedural marks (ours, CC0, 24 seeds)  — the subject again, clean silhouettes

Each image: transparent sprites are composited on the palette's poster cream; everything is
centre-cropped square, resized (NEAREST for sprites <= 64 px so pixels stay pixels, LANCZOS for
prints), then snapped to the 32 HOUSE colours. Captions: Kenney file/pack names ("tile, grass,
pixel-platformer"), Met titles, the LoRA prompt family, "hermit crab mark". The ledger row keeps
source, licence, origin URL/id and both hashes. Output: data/images/pixel_train/{32,64}/ + ledger.jsonl
+ captions.jsonl. Nothing from anywhere else goes in.

    .venv/Scripts/python.exe scripts/build_pixel_trainset.py
"""

from __future__ import annotations

import glob
import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))
from palettes import CANDIDATES, HOUSE  # noqa: E402
OUT = os.path.join(ROOT, "data", "images", "pixel_train")


def main() -> int:
    from PIL import Image
    pal = CANDIDATES[HOUSE]
    paper = pal.ramps["poster"][3]
    pal_img = Image.new("P", (1, 1))
    flat = [c for rgb in pal.colors for c in rgb] + [0] * (768 - 3 * len(pal.colors))
    pal_img.putpalette(flat)

    def snap(im: Image.Image, size: int, pixel_source: bool) -> Image.Image:
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGBA", im.size, paper + (255,))
            bg.alpha_composite(im); im = bg.convert("RGB")
        else:
            im = im.convert("RGB")
        w, h = im.size; side = min(w, h)
        im = im.crop(((w - side) // 2, (h - side) // 2, (w - side) // 2 + side, (h - side) // 2 + side))
        im = im.resize((size, size), Image.NEAREST if (pixel_source and side <= size) else Image.LANCZOS)
        q = im.quantize(palette=pal_img, dither=Image.Dither.NONE)
        return q.convert("RGB")

    rows = []
    # Kenney
    for idx in glob.glob(os.path.join(ROOT, "data", "images", "kenney", "*", "index.jsonl")):
        pack = os.path.basename(os.path.dirname(idx))
        for l in io.open(idx, encoding="utf-8"):
            if not l.strip():
                continue
            r = json.loads(l)
            words = re.sub(r"[_\-]+", " ", re.sub(r"\.png$|_r\d+_c\d+$", "", os.path.basename(r["file"]))).strip()
            rows.append({"source": "kenney", "pack": pack, "file": r["file"], "license": "CC0-1.0", "origin": f"https://kenney.nl/assets/{pack}",
                         "caption": f"pixel sprite, {words}, {pack.replace('-', ' ')}", "pixel": True, "sha256_source": r["sha256"]})
    # Met curated prints
    for l in io.open(os.path.join(ROOT, "data", "images", "train", "ledger.jsonl"), encoding="utf-8"):
        if not l.strip():
            continue
        r = json.loads(l)
        rows.append({"source": "met", "file": r["file_64"], "license": r.get("license"), "origin": r.get("object_url"),
                     "caption": f"Belle Époque print, {(r.get('title') or '')[:70]}", "pixel": False, "sha256_source": r.get("sha256_64")})
    # Library of Congress Artists Posters (public domain, pre-1929; crawl finished 2026-09-21, 1,411 items)
    loc = os.path.join(ROOT, "data", "images", "loc", "ledger.jsonl")
    if os.path.exists(loc):
        for l in io.open(loc, encoding="utf-8"):
            if not l.strip():
                continue
            r = json.loads(l)
            who = (r.get("contributors") or [""])[0].split(",")[0].strip().title()
            rows.append({"source": "loc", "file": r["file"], "license": r.get("license"), "origin": r.get("item_url"),
                         "caption": f"Belle Époque lithograph poster, {(r.get('title') or '')[:60]}" + (f", by {who}" if who else "") + (f", {r['end_year']}" if r.get("end_year") else ""),
                         "pixel": False, "sha256_source": r.get("sha256")})
    # LoRA candidates (D-75), from the 512 px originals
    for d, fam in (("crabs", "text-to-image"), ("crabs2", "img2img")):
        mp = os.path.join(ROOT, "runs", "runpod", "belle", d, "meta.json")
        if os.path.exists(mp):
            for m in json.load(io.open(mp, encoding="utf-8")):
                rows.append({"source": "lora-d75", "file": os.path.relpath(os.path.join(ROOT, "runs", "runpod", "belle", d, m["file"]), ROOT).replace("\\", "/"),
                             "license": "CC0-1.0 (generated output, O-28; LoRA CC-BY-SA-4.0 on CommonCanvas-S-C)", "origin": f"D-75 {fam} seed {m['seed']}",
                             "caption": "hermit crab mark, Belle Époque lithograph poster, medallion", "pixel": False, "sha256_source": None})
    # procedural marks
    import mark as M, artkit
    os.makedirs(os.path.join(OUT, "src_marks"), exist_ok=True)
    for s in range(24):
        img = M.mark(s, 64)
        p = os.path.join(OUT, "src_marks", f"mark_{s}.png")
        artkit.write_png(p, [[paper if px == (0, 0, 0) else px for px in row] for row in img])
        rows.append({"source": "mark", "file": os.path.relpath(p, ROOT).replace("\\", "/"), "license": "CC0-1.0 (ours)", "origin": f"app/mark.py seed {s}",
                     "caption": "hermit crab mark, retreated into its shell, medallion, poster", "pixel": True, "sha256_source": None})
    for size in (32, 64):
        os.makedirs(os.path.join(OUT, str(size)), exist_ok=True)
    kept = 0
    from collections import Counter
    c = Counter()
    with io.open(os.path.join(OUT, "ledger.jsonl"), "w", encoding="utf-8", newline="\n") as led, \
         io.open(os.path.join(OUT, "captions.jsonl"), "w", encoding="utf-8", newline="\n") as cap:
        for i, r in enumerate(rows):
            src = os.path.join(ROOT, r["file"])
            try:
                im = Image.open(src)
            except Exception:
                continue
            name = f"{r['source']}_{i:06d}.png"
            r2 = dict(r)
            for size in (32, 64):
                q = snap(im, size, r["pixel"])
                p = os.path.join(OUT, str(size), name)
                q.save(p, "PNG", optimize=True)
                r2[f"file_{size}"] = os.path.relpath(p, ROOT).replace("\\", "/")
                r2[f"sha256_{size}"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
            led.write(json.dumps(r2, ensure_ascii=False) + "\n")
            cap.write(json.dumps({"file_name": name, "text": r["caption"]}, ensure_ascii=False) + "\n")
            kept += 1; c[r["source"]] += 1
    print(f"pixel training set: {kept:,} images at 32 and 64 px in the {pal.name} palette; by source {dict(c)} -> {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

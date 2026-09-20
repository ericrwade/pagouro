"""Draw 1.0 corpus, slice two: Kenney's CC0 pixel-art packs (D-67 / IMAGE_MVP.md). Standard library only.

Every kenney.nl asset page states "CC0 licensed" and links one zip; this script reads the page,
records the licence line it found, downloads the zip once (skipped if present), unpacks the PNGs
that are sprites or tiles (both sides <= --max-px; sheets and previews are skipped), and writes
data/images/kenney/ledger.jsonl: one row per pack (slug, page URL, zip URL, zip sha256, bytes,
licence text as found, n_images) and data/images/kenney/<slug>/index.jsonl listing each image
with its size and sha256. Polite: one request at a time, a pause between packs.

    python scripts/fetch_kenney.py                 # the default pack list
    python scripts/fetch_kenney.py --packs tiny-town 1-bit-pack
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import struct
import time
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "images", "kenney")
UA = {"User-Agent": "pagouro-corpus-builder/1.0 (+https://github.com/ericrwade/pagouro)"}
PACKS = ["pixel-platformer", "pixel-platformer-industrial-expansion", "pixel-platformer-farm-expansion",
         "pixel-platformer-food-expansion", "pixel-platformer-blocks", "tiny-town", "tiny-dungeon", "tiny-ski",
         "tiny-battle", "micro-roguelike", "1-bit-pack", "bit-pack", "pixel-shmup", "pixel-ui-pack",
         "roguelike-characters", "roguelike-caves-dungeons", "roguelike-city-pack", "roguelike-indoors",
         "roguelike-modern-city", "roguelike-rpg-pack", "sokoban", "tiny-tower", "pixel-line-icons",
         "monochrome-rpg", "1-bit-input-prompts-pixel-16", "space-shooter-extension", "pixel-vehicle-pack",
         "fish-pack", "animal-pack-redux", "creature-mixer"]


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
        return r.read()


def png_size(data: bytes):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packs", nargs="*", default=PACKS)
    ap.add_argument("--max-px", type=int, default=128)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    led_path = os.path.join(OUT, "ledger.jsonl")
    have = set()
    if os.path.exists(led_path):
        for line in io.open(led_path, encoding="utf-8"):
            if line.strip():
                have.add(json.loads(line)["slug"])
    total = 0
    with io.open(led_path, "a", encoding="utf-8", newline="\n") as led:
        for slug in a.packs:
            if slug in have:
                continue
            page = f"https://kenney.nl/assets/{slug}"
            try:
                html = get(page).decode("utf-8", "replace")
            except Exception as e:  # noqa: BLE001
                print(f"  {slug}: page failed ({str(e)[:60]})"); continue
            m = re.search(r"href='(https://kenney\.nl/media/pages/assets/[^']+\.zip)'", html)
            lic = re.search(r"([^'>]{0,80}CC0[^'<]{0,40})", html)
            if not m:
                print(f"  {slug}: no zip link on the page"); continue
            if not lic:
                print(f"  {slug}: no CC0 statement found on the page; skipped"); continue
            zurl = m.group(1)
            zpath = os.path.join(OUT, f"{slug}.zip")
            if not os.path.exists(zpath):
                data = get(zurl)
                io.open(zpath, "wb").write(data)
                time.sleep(2.0)
            data = open(zpath, "rb").read()
            pack_dir = os.path.join(OUT, slug)
            os.makedirs(pack_dir, exist_ok=True)
            n = 0
            with zipfile.ZipFile(io.BytesIO(data)) as z, io.open(os.path.join(pack_dir, "index.jsonl"), "w", encoding="utf-8", newline="\n") as idx:
                for info in z.infolist():
                    name = info.filename
                    if not name.lower().endswith(".png") or info.file_size > 400_000:
                        continue
                    low = name.lower()
                    if any(k in low for k in ("preview", "sample", "sheet", "spritesheet", "tilemap", "tilesheet")):
                        continue
                    b = z.read(info)
                    sz = png_size(b)
                    if not sz or max(sz) > a.max_px or min(sz) < 4:
                        continue
                    rel = re.sub(r"[^A-Za-z0-9_.\-]+", "_", name)
                    p = os.path.join(pack_dir, rel)
                    io.open(p, "wb").write(b)
                    idx.write(json.dumps({"file": os.path.relpath(p, ROOT).replace("\\", "/"), "zip_path": name,
                                          "width": sz[0], "height": sz[1], "sha256": hashlib.sha256(b).hexdigest()}) + "\n")
                    n += 1
            row = {"slug": slug, "page_url": page, "zip_url": zurl, "zip_sha256": hashlib.sha256(data).hexdigest(),
                   "zip_bytes": len(data), "license": "CC0-1.0", "license_as_found": lic.group(1).strip(),
                   "author": "Kenney (kenney.nl)", "n_images": n, "max_px": a.max_px, "retrieved": time.strftime("%Y-%m-%d")}
            led.write(json.dumps(row, ensure_ascii=False) + "\n"); led.flush()
            total += n
            print(f"  {slug}: {n} sprites/tiles <= {a.max_px}px from {len(data) // 1024} KB zip", flush=True)
            time.sleep(1.5)
    print(f"done: {total:,} images this run; ledger {os.path.relpath(led_path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

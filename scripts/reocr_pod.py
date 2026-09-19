"""Re-OCR archive.org scans with LightOnOCR-2-1B on a GPU pod (D-66).

For each item: page count from archive.org, page JPEGs via the BookReader endpoint
(page/n{N}_w1400.jpg, a few at a time, polite), then LightOnOCR in batches, one Markdown file per
item with `<!-- page N -->` markers, plus a JSON of per-page stats. Resumable: pages already
OCR'd are skipped.

    python scripts/reocr_pod.py --out /workspace/reocr --items PilotsHandbookOfAeronauticalKnowledge NEETSModule01 ...
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "pagouro-corpus-builder/1.0 (+https://github.com/ericrwade/pagouro)"}


def get(url: str, tries: int = 4) -> bytes:
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))
    return b""


def page_count(item: str) -> int:
    m = json.loads(get(f"https://archive.org/metadata/{item}"))
    n = m.get("metadata", {}).get("imagecount")
    if n:
        return int(n)
    for f in m.get("files", []):
        if f["name"].endswith("_scandata.xml"):
            xml = get(f"https://archive.org/download/{item}/{f['name']}").decode("utf-8", "replace")
            return xml.count("<page ")
    raise RuntimeError(f"{item}: no page count")


def fetch_pages(item: str, n: int, d: str, width: int = 1400, workers: int = 4) -> list[str]:
    os.makedirs(d, exist_ok=True)

    def one(i: int) -> str:
        p = os.path.join(d, f"p{i:04d}.jpg")
        if os.path.exists(p) and os.path.getsize(p) > 2000:
            return p
        try:
            data = get(f"https://archive.org/download/{item}/page/n{i}_w{width}.jpg")
            if data[:2] == b"\xff\xd8":
                io.open(p, "wb").write(data)
                return p
        except Exception:
            pass
        return ""

    with ThreadPoolExecutor(workers) as ex:
        paths = list(ex.map(one, range(n)))
    return [p for p in paths if p]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", nargs="+", required=True)
    ap.add_argument("--out", default="/workspace/reocr")
    ap.add_argument("--model", default="lightonai/LightOnOCR-2-1B")
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--max-new-tokens", type=int, default=2048)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    import torch
    from PIL import Image
    from transformers import LightOnOcrForConditionalGeneration, LightOnOcrProcessor
    device = "cuda"
    proc = LightOnOcrProcessor.from_pretrained(a.model)
    model = LightOnOcrForConditionalGeneration.from_pretrained(a.model, dtype=torch.bfloat16).to(device).eval()
    for item in a.items:
        t0 = time.time()
        n = page_count(item)
        d = os.path.join(a.out, item)
        pages = fetch_pages(item, n, os.path.join(d, "pages"))
        print(f"{item}: {len(pages)}/{n} pages fetched in {time.time()-t0:.0f}s", flush=True)
        done_dir = os.path.join(d, "md"); os.makedirs(done_dir, exist_ok=True)
        todo = [p for p in pages if not os.path.exists(os.path.join(done_dir, os.path.basename(p)[:-4] + ".md"))]
        stats = {"item": item, "pages_total": n, "pages_fetched": len(pages), "chars": 0, "failed": []}
        t1 = time.time()
        for b0 in range(0, len(todo), a.batch):
            chunk = todo[b0:b0 + a.batch]
            imgs = [Image.open(p).convert("RGB") for p in chunk]
            try:
                convs = [[{"role": "user", "content": [{"type": "image", "image": im}]}] for im in imgs]
                inputs = proc.apply_chat_template(convs, add_generation_prompt=True, tokenize=True,
                                                  return_dict=True, return_tensors="pt", padding=True).to(device)
                if "pixel_values" in inputs:
                    inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)
                with torch.no_grad():
                    out = model.generate(**inputs, max_new_tokens=a.max_new_tokens, do_sample=False)
                texts = proc.batch_decode(out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            except Exception as e:  # noqa: BLE001
                # fall back to one at a time for this chunk
                texts = []
                for im in imgs:
                    try:
                        conv = [[{"role": "user", "content": [{"type": "image", "image": im}]}]]
                        inputs = proc.apply_chat_template(conv, add_generation_prompt=True, tokenize=True,
                                                          return_dict=True, return_tensors="pt").to(device)
                        if "pixel_values" in inputs:
                            inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)
                        with torch.no_grad():
                            out = model.generate(**inputs, max_new_tokens=a.max_new_tokens, do_sample=False)
                        texts.append(proc.batch_decode(out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)[0])
                    except Exception as e2:  # noqa: BLE001
                        texts.append(""); stats["failed"].append(str(e2)[:80])
            for p, t in zip(chunk, texts):
                io.open(os.path.join(done_dir, os.path.basename(p)[:-4] + ".md"), "w", encoding="utf-8", newline="\n").write(t)
                stats["chars"] += len(t)
            if (b0 // a.batch) % 10 == 0:
                rate = (b0 + len(chunk)) / max(1e-6, time.time() - t1)
                print(f"  {item}: {b0 + len(chunk)}/{len(todo)} pages, {rate:.2f} pages/s", flush=True)
        # assemble
        parts = []
        for p in pages:
            mdp = os.path.join(done_dir, os.path.basename(p)[:-4] + ".md")
            if os.path.exists(mdp):
                idx = int(os.path.basename(p)[1:5])
                parts.append(f"<!-- page {idx} -->\n" + io.open(mdp, encoding="utf-8").read().strip() + "\n")
        io.open(os.path.join(a.out, f"{item}.md"), "w", encoding="utf-8", newline="\n").write("\n".join(parts))
        stats["seconds"] = round(time.time() - t0, 1)
        io.open(os.path.join(a.out, f"{item}.stats.json"), "w", encoding="utf-8").write(json.dumps(stats, indent=1))
        print(f"{item}: done, {stats['chars']:,} chars, {stats['seconds']}s, {len(stats['failed'])} failed", flush=True)
    print("REOCR_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

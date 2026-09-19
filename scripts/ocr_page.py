"""OCR page images with LightOnOCR (Apache-2.0) through transformers>=5 -- the O-26 test.

    python scripts/ocr_page.py page1.jpg page2.jpg --out-dir ocr_out [--model lightonai/LightOnOCR-2-1B]

Writes <out-dir>/<image-stem>.md and prints timing. GPU if available; CPU works but is slow.
The output's rights are the source page's; the OCR engine and model version go on the ledger row.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import torch
from PIL import Image
from transformers import LightOnOcrForConditionalGeneration, LightOnOcrProcessor


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--model", default="lightonai/LightOnOCR-2-1B")
    ap.add_argument("--out-dir", default="ocr_out")
    ap.add_argument("--max-new-tokens", type=int, default=2048)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    t0 = time.time()
    processor = LightOnOcrProcessor.from_pretrained(a.model)
    model = LightOnOcrForConditionalGeneration.from_pretrained(a.model, dtype=dtype).to(device).eval()
    print(f"loaded {a.model} on {device} in {time.time() - t0:.1f}s", flush=True)
    for path in a.images:
        t = time.time()
        img = Image.open(path).convert("RGB")
        conv = [{"role": "user", "content": [{"type": "image", "image": img}]}]
        inputs = processor.apply_chat_template(conv, add_generation_prompt=True, tokenize=True,
                                               return_dict=True, return_tensors="pt").to(device)
        if "pixel_values" in inputs:
            inputs["pixel_values"] = inputs["pixel_values"].to(dtype)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=a.max_new_tokens, do_sample=False)
        text = processor.batch_decode(out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)[0]
        stem = os.path.splitext(os.path.basename(path))[0]
        with open(os.path.join(a.out_dir, stem + ".md"), "w", encoding="utf-8") as f:
            f.write(text)
        print(f"{path}: {len(text):,} chars in {time.time() - t:.1f}s -> {a.out_dir}/{stem}.md", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Re-OCR with LightOnOCR-2-1B through vLLM (batched, the model card's recommended path). D-66.

Pages must already be fetched (scripts/reocr_pod.py does the fetching; this script OCRs the
`pages/` folders it left behind and writes the same md/ layout and assembled .md per item).

    python scripts/reocr_vllm.py --root /workspace/reocr --items NEETSModule13 ... [--gpu-mem 0.5]
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/workspace/reocr")
    ap.add_argument("--items", nargs="+", required=True)
    ap.add_argument("--model", default="lightonai/LightOnOCR-2-1B")
    ap.add_argument("--gpu-mem", type=float, default=0.5)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--limit", type=int, default=0, help="test: only this many pages per item")
    a = ap.parse_args()
    from PIL import Image
    from vllm import LLM, SamplingParams
    llm = LLM(model=a.model, gpu_memory_utilization=a.gpu_mem, max_model_len=6144, limit_mm_per_prompt={"image": 1}, trust_remote_code=True)
    sp = SamplingParams(temperature=0.0, max_tokens=a.max_tokens)
    for item in a.items:
        d = os.path.join(a.root, item)
        pages = sorted(p for p in os.listdir(os.path.join(d, "pages")) if p.endswith(".jpg"))
        if a.limit:
            pages = pages[:a.limit]
        md = os.path.join(d, "md"); os.makedirs(md, exist_ok=True)
        todo = [p for p in pages if not os.path.exists(os.path.join(md, p[:-4] + ".md"))]
        t0 = time.time(); chars = 0
        for b0 in range(0, len(todo), a.batch):
            chunk = todo[b0:b0 + a.batch]
            msgs = [[{"role": "user", "content": [{"type": "image_pil", "image_pil": Image.open(os.path.join(d, "pages", p)).convert("RGB")}]}] for p in chunk]
            outs = llm.chat(msgs, sp, use_tqdm=False)
            for p, o in zip(chunk, outs):
                t = o.outputs[0].text
                io.open(os.path.join(md, p[:-4] + ".md"), "w", encoding="utf-8", newline="\n").write(t)
                chars += len(t)
            done = b0 + len(chunk)
            print(f"  {item}: {done}/{len(todo)} pages, {done / (time.time() - t0):.2f} pages/s", flush=True)
        parts = []
        for p in pages:
            mp = os.path.join(md, p[:-4] + ".md")
            if os.path.exists(mp):
                parts.append(f"<!-- page {int(p[1:5])} -->\n" + io.open(mp, encoding="utf-8").read().strip() + "\n")
        io.open(os.path.join(a.root, f"{item}.md"), "w", encoding="utf-8", newline="\n").write("\n".join(parts))
        io.open(os.path.join(a.root, f"{item}.stats.json"), "w", encoding="utf-8").write(json.dumps(
            {"item": item, "pages": len(pages), "ocr_pages": len(parts), "chars": chars, "seconds": round(time.time() - t0, 1),
             "engine": f"vLLM + {a.model}"}, indent=1))
        print(f"{item}: done, {len(parts)} pages, {time.time() - t0:.0f}s", flush=True)
    print("REOCR_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

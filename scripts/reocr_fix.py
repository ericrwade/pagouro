"""Re-OCR the leaves that batched generation contaminated (D-66 audit, 2026-09-20).

Finding: with LightOnOCR-2-1B under transformers 5.17, batch 8, left padding, the first two
pages of every batch start correctly and then continue with text from the previous batch's
pages 4-5 (their footers prove it: leaf 22 of NEETS module 1 is page 1-11 and ends "1-7").
Positions 2-7 check clean by footer. This script redoes, one page at a time (no batching), every
leaf at batch position 0 or 1 plus every leaf whose ending text is a verbatim copy of an earlier
page, then reassembles <item>.md and records what it redid in <item>.stats.json.

    python reocr_fix.py --out /workspace/reocr --batch-start 6 --items NEETSModule01 ...
    python reocr_fix.py ... --only 22 23 --items NEETSModule01      # test on named leaves
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time


def tail_copies(md_dir: str) -> set[int]:
    t = {}
    for f in os.listdir(md_dir):
        if f.endswith(".md"):
            t[int(f[1:5])] = io.open(os.path.join(md_dir, f), encoding="utf-8").read().strip()
    bad = set()
    for i, s in t.items():
        if len(s) < 400:
            continue
        tail = s[-200:]
        for j in range(max(0, i - 8), i):
            if j in t and tail in t[j]:
                bad.add(i)
                break
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", nargs="+", required=True)
    ap.add_argument("--out", default="/workspace/reocr")
    ap.add_argument("--model", default="lightonai/LightOnOCR-2-1B")
    ap.add_argument("--batch-start", type=int, default=6, help="leaf index where the batched run's first batch began")
    ap.add_argument("--batch", type=int, default=8, help="the batched run's batch size")
    ap.add_argument("--only", nargs="*", type=int, help="test: only these leaves")
    ap.add_argument("--max-new-tokens", type=int, default=1536)
    a = ap.parse_args()
    import torch
    from PIL import Image
    from transformers import LightOnOcrForConditionalGeneration, LightOnOcrProcessor
    proc = LightOnOcrProcessor.from_pretrained(a.model)
    model = LightOnOcrForConditionalGeneration.from_pretrained(a.model, dtype=torch.bfloat16).to("cuda").eval()
    for item in a.items:
        d = os.path.join(a.out, item)
        md_dir, pg_dir = os.path.join(d, "md"), os.path.join(d, "pages")
        leaves = sorted(int(f[1:5]) for f in os.listdir(pg_dir) if f.endswith(".jpg"))
        if a.only:
            redo = [i for i in leaves if i in set(a.only)]
        else:
            pos01 = {i for i in leaves if i >= a.batch_start and (i - a.batch_start) % a.batch in (0, 1)}
            copies = tail_copies(md_dir)
            redo = sorted(pos01 | copies)
            print(f"{item}: {len(leaves)} leaves; batch positions 0/1: {len(pos01)}; tail copies: {len(copies)}; redo {len(redo)}", flush=True)
        t0 = time.time()
        for k, i in enumerate(redo, 1):
            im = Image.open(os.path.join(pg_dir, f"p{i:04d}.jpg")).convert("RGB")
            conv = [[{"role": "user", "content": [{"type": "image", "image": im}]}]]
            inputs = proc.apply_chat_template(conv, add_generation_prompt=True, tokenize=True,
                                              return_dict=True, return_tensors="pt").to("cuda")
            if "pixel_values" in inputs:
                inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)
            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=a.max_new_tokens, do_sample=False)
            text = proc.batch_decode(out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)[0]
            io.open(os.path.join(md_dir, f"p{i:04d}.md"), "w", encoding="utf-8", newline="\n").write(text)
            if k % 20 == 0 or k == len(redo):
                print(f"  {item}: {k}/{len(redo)} redone, {k / max(1e-6, time.time() - t0):.2f} pages/s", flush=True)
        # reassemble
        parts = []
        for i in leaves:
            mdp = os.path.join(md_dir, f"p{i:04d}.md")
            if os.path.exists(mdp):
                parts.append(f"<!-- page {i} -->\n" + io.open(mdp, encoding="utf-8").read().strip() + "\n")
        io.open(os.path.join(a.out, f"{item}.md"), "w", encoding="utf-8", newline="\n").write("\n".join(parts))
        sp = os.path.join(a.out, f"{item}.stats.json")
        stats = json.load(io.open(sp, encoding="utf-8")) if os.path.exists(sp) else {"item": item}
        stats["fix_2026_09_20"] = {"redone_leaves": len(redo), "reason": "batched generation contaminated batch positions 0-1; redone unbatched",
                                   "seconds": round(time.time() - t0, 1)}
        stats["chars"] = sum(len(p) for p in parts)
        io.open(sp, "w", encoding="utf-8").write(json.dumps(stats, indent=1))
        print(f"{item}: reassembled, {stats['chars']:,} chars", flush=True)
    print("REOCR_FIX_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

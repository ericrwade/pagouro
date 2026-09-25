"""Weight-space average of two checkpoints of the same architecture (a "model soup", Wortsman et
al. 2022): out = (1-alpha) * A + alpha * B, tensor by tensor. Used after GRPO-1 on the 1B
(2026-09-25, D-88): the policy-gradient run cut fabrication 64% -> 19% but its abstention reflex
leaked into argument prompts and its long outputs looped; averaging with the SFT it started from
keeps part of the gain with less drift, and costs nothing but a desk CPU.

    python scripts/soup.py --a data/out_1b/pagouro-1b-sftB.pt --b data/out_1b/grpo/pagouro-1b-grpo.pt \
        --alpha 0.5 --out data/out_1b/grpo/pagouro-1b-soup50.pt

Memory: both inputs are opened with mmap (paged, not loaded), the output is built tensor by tensor;
peak RSS is about one model's worth of f32 (3.9 GB for the 1B), which fits beside Eric's other apps.
Optimizer state is dropped (a soup has no optimizer); config/meta come from A.
"""
from __future__ import annotations

import argparse
import sys

import torch


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="base checkpoint (weight 1-alpha)")
    ap.add_argument("--b", required=True, help="the other checkpoint (weight alpha)")
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ca = torch.load(a.a, map_location="cpu", weights_only=False, mmap=True)
    cb = torch.load(a.b, map_location="cpu", weights_only=False, mmap=True)
    sa, sb = ca["model"], cb["model"]
    if sa.keys() != sb.keys():
        print("key sets differ", file=sys.stderr)
        return 1
    out = {}
    n = 0
    for k in sa:
        ta, tb = sa[k], sb[k]
        if ta.shape != tb.shape:
            print(f"shape mismatch at {k}: {tuple(ta.shape)} vs {tuple(tb.shape)}", file=sys.stderr)
            return 1
        out[k] = ((1.0 - a.alpha) * ta.float() + a.alpha * tb.float()).to(ta.dtype).contiguous()
        n += out[k].numel()
    ck = {"model": out, "step": ca.get("step"), "config": ca["config"], "val_loss": ca.get("val_loss"),
          "meta": ca.get("meta"), "soup": {"a": a.a, "b": a.b, "alpha": a.alpha}}
    torch.save(ck, a.out)
    print(f"soup written: {a.out}  alpha={a.alpha}  tensors={len(out)}  params={n:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

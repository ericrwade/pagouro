"""Loss / perplexity of a checkpoint on held-out token files, scored SEQUENTIALLY (every window
once, no random sampling) so two checkpoints are compared on exactly the same tokens.

    python scripts/score_heldout.py --ckpt /workspace/ckpt/flash.pt \\
        --data /workspace/data/flash/val.bin --data data/tokenized_anneal/val.bin \\
        --data data/tokenized_anneal_shelf/val.bin --seq-len 1024 --out runs/heldout_flash.json

Writes {"ckpt", "step", "sets": {path: {"tokens", "loss", "ppl"}}}. Used for the D-58 ablation
(shelf vs no-shelf) and any later A/B where the training-time val numbers are not comparable
because each arm has its own val set.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pagouro.model import Pagouro, ModelConfig  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--data", action="append", required=True, help="val.bin (uint16); repeatable")
    ap.add_argument("--seq-len", type=int, default=1024)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--max-windows", type=int, default=0, help="cap windows per set (0 = all)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    ck = torch.load(a.ckpt, map_location=device, weights_only=False)
    cfg = ModelConfig(**ck["config"]) if isinstance(ck.get("config"), dict) else ck["config"]
    model = Pagouro(cfg).to(device)
    model.load_state_dict(ck["model"])
    model.eval()
    use_amp = device == "cuda"
    result = {"ckpt": a.ckpt, "step": ck.get("step"), "seq_len": a.seq_len, "sets": {}}
    for path in a.data:
        data = np.memmap(path, dtype=np.uint16, mode="r")
        n_win = (len(data) - 1) // a.seq_len
        if a.max_windows:
            n_win = min(n_win, a.max_windows)
        tot_loss, tot_tok = 0.0, 0
        with torch.no_grad():
            for b0 in range(0, n_win, a.batch_size):
                idx = range(b0, min(n_win, b0 + a.batch_size))
                x = np.stack([data[i * a.seq_len: i * a.seq_len + a.seq_len].astype(np.int64) for i in idx])
                y = np.stack([data[i * a.seq_len + 1: i * a.seq_len + 1 + a.seq_len].astype(np.int64) for i in idx])
                x, y = torch.from_numpy(x).to(device), torch.from_numpy(y).to(device)
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=use_amp):
                    _, loss = model(x, targets=y)
                tot_loss += loss.item() * y.numel()
                tot_tok += y.numel()
        mean = tot_loss / max(1, tot_tok)
        result["sets"][path] = {"tokens": tot_tok, "loss": round(mean, 4), "ppl": round(math.exp(mean), 2)}
        print(f"{path}: {tot_tok:,} tokens  loss {mean:.4f}  ppl {math.exp(mean):.2f}", flush=True)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        io.open(a.out, "w", encoding="utf-8", newline="\n").write(json.dumps(result, indent=2) + "\n")
        print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

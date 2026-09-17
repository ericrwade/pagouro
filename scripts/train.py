"""Training loop with checkpointing, resume and loss logging.

Every long-running process in this project must be resumable and must write progress
to a file a human can glance at (brief section 13). Resume is proven by killing a run
and restarting it, not by trusting that it works.

The data loader shifts targets by one position. This matters: with unshifted targets
the model can see the token it is meant to predict, loss collapses below the entropy
floor, and the run looks excellent while learning nothing.

Usage:
    python scripts/train.py --max-steps 2000
    python scripts/train.py --resume            # continues from the latest checkpoint
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import time

import numpy as np
import torch

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pagouro.model import Pagouro, ModelConfig  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "tokenized")
CKPT_DIR = os.path.join(ROOT, "checkpoints")
LOG_PATH = os.path.join(ROOT, "runs", "train_log.jsonl")


def get_batch(data: np.memmap, batch_size: int, seq_len: int, device: str, rng: np.random.Generator):
    # +1 so the target can be shifted one position right.
    ix = rng.integers(0, len(data) - seq_len - 1, size=batch_size)
    x = np.stack([data[i : i + seq_len].astype(np.int64) for i in ix])
    y = np.stack([data[i + 1 : i + 1 + seq_len].astype(np.int64) for i in ix])
    return torch.from_numpy(x).to(device), torch.from_numpy(y).to(device)


def lr_at(step: int, warmup: int, total: int, lr_max: float, lr_min: float) -> float:
    if step < warmup:
        return lr_max * (step + 1) / warmup
    if step >= total:
        return lr_min
    progress = (step - warmup) / max(1, total - warmup)
    return lr_min + 0.5 * (lr_max - lr_min) * (1 + math.cos(math.pi * progress))


@torch.no_grad()
def estimate_loss(model, data, batch_size, seq_len, device, rng, iters=20):
    model.eval()
    losses = []
    for _ in range(iters):
        x, y = get_batch(data, batch_size, seq_len, device, rng)
        _, loss = model(x, targets=y)
        losses.append(loss.item())
    model.train()
    return float(np.mean(losses))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dim", type=int, default=384)
    ap.add_argument("--layers", type=int, default=6)
    ap.add_argument("--heads", type=int, default=6)
    ap.add_argument("--kv-heads", type=int, default=2)
    ap.add_argument("--seq-len", type=int, default=256)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--max-steps", type=int, default=2000)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--min-lr", type=float, default=3e-5)
    ap.add_argument("--warmup", type=int, default=100)
    ap.add_argument("--weight-decay", type=float, default=0.1)
    ap.add_argument("--grad-clip", type=float, default=1.0)
    ap.add_argument("--eval-every", type=int, default=200)
    ap.add_argument("--ckpt-every", type=int, default=250)
    ap.add_argument("--threads", type=int, default=0, help="0 = torch default")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--seed", type=int, default=1337)
    # Paths are arguments so the ablation pilot can run isolated arms without
    # clobbering the main run's data, checkpoint or log.
    ap.add_argument("--data-dir", default=DATA_DIR)
    ap.add_argument("--ckpt", default=os.path.join(CKPT_DIR, "latest.pt"))
    ap.add_argument("--log", default=LOG_PATH)
    a = ap.parse_args()

    if a.threads:
        torch.set_num_threads(a.threads)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    os.makedirs(CKPT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(a.log) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(a.ckpt) or ".", exist_ok=True)

    meta_path = os.path.join(a.data_dir, "meta.json")
    if not os.path.exists(meta_path):
        raise SystemExit("no tokenized data. Run scripts/tokenize_corpus.py first.")
    with io.open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    train_data = np.memmap(os.path.join(a.data_dir, "train.bin"), dtype=np.uint16, mode="r")
    val_data = np.memmap(os.path.join(a.data_dir, "val.bin"), dtype=np.uint16, mode="r")

    cfg = ModelConfig(
        vocab_size=meta["vocab_size"], dim=a.dim, n_layers=a.layers,
        n_heads=a.heads, n_kv_heads=a.kv_heads, max_seq_len=a.seq_len,
    )
    model = Pagouro(cfg).to(device)

    decay = [p for p in model.parameters() if p.dim() >= 2]
    no_decay = [p for p in model.parameters() if p.dim() < 2]
    opt = torch.optim.AdamW(
        [{"params": decay, "weight_decay": a.weight_decay},
         {"params": no_decay, "weight_decay": 0.0}],
        lr=a.lr, betas=(0.9, 0.95), eps=1e-8,
    )

    start_step = 0
    ckpt_path = a.ckpt
    if a.resume:
        if not os.path.exists(ckpt_path):
            raise SystemExit(f"--resume given but no checkpoint at {ckpt_path}")
        ck = torch.load(ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(ck["model"])
        opt.load_state_dict(ck["optimizer"])
        start_step = ck["step"] + 1
        print(f"RESUMED from step {ck['step']} (val loss {ck.get('val_loss', float('nan')):.4f})")

    rng = np.random.default_rng(a.seed + start_step)

    print(f"device       : {device} ({torch.get_num_threads()} threads)")
    print(f"parameters   : {model.num_parameters():,} "
          f"({model.num_parameters(non_embedding=True):,} non-embedding)")
    print(f"tokens avail : {meta['train_tokens']:,} train / {meta['val_tokens']:,} val")
    print(f"tokens/step  : {a.batch_size * a.seq_len:,}")
    print(f"steps        : {start_step} -> {a.max_steps}")
    print(f"log          : {os.path.relpath(a.log, ROOT)}\n")

    log = io.open(a.log, "a", encoding="utf-8", newline="\n")
    model.train()
    t0 = time.time()
    tokens_seen = start_step * a.batch_size * a.seq_len
    best_val = float("inf")

    for step in range(start_step, a.max_steps):
        lr = lr_at(step, a.warmup, a.max_steps, a.lr, a.min_lr)
        for g in opt.param_groups:
            g["lr"] = lr

        x, y = get_batch(train_data, a.batch_size, a.seq_len, device, rng)
        _, loss = model(x, targets=y)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        gnorm = torch.nn.utils.clip_grad_norm_(model.parameters(), a.grad_clip)
        opt.step()

        tokens_seen += a.batch_size * a.seq_len

        if step % 20 == 0 or step == a.max_steps - 1:
            el = time.time() - t0
            tps = (tokens_seen - start_step * a.batch_size * a.seq_len) / max(el, 1e-9)
            rec = {"step": step, "loss": round(loss.item(), 4), "lr": round(lr, 7),
                   "grad_norm": round(float(gnorm), 3), "tokens": tokens_seen,
                   "elapsed_s": round(el, 1), "tokens_per_s": round(tps, 1)}
            log.write(json.dumps(rec) + "\n")
            log.flush()
            print(f"step {step:6d} | loss {loss.item():7.4f} | lr {lr:.2e} | "
                  f"gnorm {float(gnorm):5.2f} | {tps:7.0f} tok/s | {el:6.1f}s", flush=True)

        if (step + 1) % a.eval_every == 0 or step == a.max_steps - 1:
            vl = estimate_loss(model, val_data, a.batch_size, a.seq_len, device, rng)
            best_val = min(best_val, vl)
            rec = {"step": step, "val_loss": round(vl, 4), "val_ppl": round(math.exp(vl), 2)}
            log.write(json.dumps(rec) + "\n")
            log.flush()
            print(f"  >> val loss {vl:.4f}  perplexity {math.exp(vl):.1f}", flush=True)

        if (step + 1) % a.ckpt_every == 0 or step == a.max_steps - 1:
            # Write to a sibling temp file and rename over the old checkpoint.
            # torch.save straight onto ckpt_path truncates it first, so a crash
            # mid-write (the 2026-09-17 hard freeze landed ten minutes after a
            # save) would leave the ONLY checkpoint of the run half-written.
            # os.replace is atomic on NTFS; the old file survives until the new
            # one is complete.
            tmp_path = ckpt_path + ".tmp"
            torch.save({
                "model": model.state_dict(),
                "optimizer": opt.state_dict(),
                "step": step,
                "config": cfg.to_dict(),
                "val_loss": best_val,
                "meta": meta,
            }, tmp_path)
            os.replace(tmp_path, ckpt_path)
            print(f"  >> checkpoint saved at step {step}", flush=True)

    log.close()
    print(f"\ndone in {time.time()-t0:.1f}s. best val loss {best_val:.4f} "
          f"(perplexity {math.exp(best_val):.1f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Supervised fine-tuning: loss computed ONLY on assistant response tokens.

Brief section 7: full fine-tune (no LoRA needed at this size), low learning
rate (10-50x lower than pretraining), 1-3 epochs, loss on response tokens only.
Loss on the user turn would teach the model to predict QUESTIONS, which is not
the goal and dilutes the actual training signal.

Reads sft/abstention_seed.jsonl (hand-written, D-11 balance) and
sft/crypto_synthetic.jsonl (DeepSeek-generated locally, D-30) and applies the
same chat template the tokenizer and the shipped app both use, so training
format and inference format can never drift apart.

    python scripts/train_sft.py --checkpoint checkpoints/latest.pt --steps 2000
"""

from __future__ import annotations

import argparse
import glob
import io
import json
import math
import os
import random
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pagouro.model import Pagouro, ModelConfig  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_examples() -> list[tuple[str, str]]:
    """Return (user_content, assistant_content) pairs from every SFT source."""
    out = []
    p1 = os.path.join(ROOT, "sft", "abstention_seed.jsonl")
    if os.path.exists(p1):
        for line in io.open(p1, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            msgs = d["messages"]
            out.append((msgs[0]["content"], msgs[1]["content"]))

    p2 = os.path.join(ROOT, "sft", "crypto_synthetic.jsonl")
    if os.path.exists(p2):
        for line in io.open(p2, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            out.append((d["question"], d["answer"]))

    # Synthesis seed (sft/build_synthesis_seed.py): comparisons and judgements
    # answered plainly, plus a few real-vs-invented mixed items. Same message
    # format as the abstention seed. Added 2026-09-17 because every confident
    # example in the abstention seed was a definition; see that file's docstring.
    p3 = os.path.join(ROOT, "sft", "synthesis_seed.jsonl")
    if os.path.exists(p3):
        for line in io.open(p3, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            msgs = d["messages"]
            out.append((msgs[0]["content"], msgs[1]["content"]))
    return out


def build_example_ids(tok, user: str, assistant: str, eot_id: int, im_start: int, im_end: int):
    """Tokenize one chat example and return (input_ids, label_ids) with the user
    turn and control tokens masked to -100 so loss only touches the response."""
    user_ids = tok.encode(f"user\n{user}").ids
    asst_ids = tok.encode(f"assistant\n{assistant}").ids

    ids = ([im_start] + user_ids + [im_end] +
           [im_start] + asst_ids + [im_end])
    labels = ([-100] * (1 + len(user_ids) + 1) +
              [-100] +                       # the "<|im_start|>" opening assistant's turn
              asst_ids + [im_end])           # loss on the actual response + its closing tag
    assert len(ids) == len(labels)
    return ids, labels


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default=os.path.join(ROOT, "checkpoints", "latest.pt"))
    ap.add_argument("--tokenizer", default=os.path.join(ROOT, "data", "tokenizer", "tokenizer.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "checkpoints", "sft.pt"))
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--lr", type=float, default=2e-5)   # 10-50x lower than pretrain (brief sec.7)
    ap.add_argument("--warmup", type=int, default=30)
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--log", default=os.path.join(ROOT, "runs", "sft_log.jsonl"))
    a = ap.parse_args()

    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(a.tokenizer)
    im_start = tok.token_to_id("<|im_start|>")
    im_end = tok.token_to_id("<|im_end|>")
    eot = tok.token_to_id("<|endoftext|>")
    if im_start is None or im_end is None:
        raise SystemExit("tokenizer is missing chat tokens; wrong tokenizer file?")

    examples = load_examples()
    if not examples:
        raise SystemExit("no SFT examples found in sft/*.jsonl")
    print(f"loaded {len(examples)} SFT examples")

    ck = torch.load(a.checkpoint, map_location="cpu", weights_only=False)
    cfg = ModelConfig(**ck["config"])
    model = Pagouro(cfg)
    model.load_state_dict(ck["model"])
    print(f"resuming from base checkpoint at step {ck['step']}, "
          f"{model.num_parameters():,} params, max_seq_len={cfg.max_seq_len}")

    # Pre-tokenize everything once; SFT sets are small enough to fit in memory.
    tokenized = []
    too_long = 0
    for user, asst in examples:
        ids, labels = build_example_ids(tok, user, asst, eot, im_start, im_end)
        if len(ids) > cfg.max_seq_len:
            too_long += 1
            continue
        tokenized.append((ids, labels))
    print(f"tokenized {len(tokenized)} examples ({too_long} skipped, too long for "
          f"max_seq_len={cfg.max_seq_len})")
    if not tokenized:
        raise SystemExit("nothing left to train on after length filtering")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    model.train()
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, betas=(0.9, 0.95), weight_decay=0.0)

    rng = random.Random(a.seed)
    os.makedirs(os.path.dirname(a.log), exist_ok=True)
    log = io.open(a.log, "w", encoding="utf-8", newline="\n")

    def get_batch(bs: int):
        batch = [rng.choice(tokenized) for _ in range(bs)]
        max_len = max(len(ids) for ids, _ in batch)
        x = torch.full((bs, max_len), eot, dtype=torch.long)
        y = torch.full((bs, max_len), -100, dtype=torch.long)
        for i, (ids, labels) in enumerate(batch):
            x[i, :len(ids)] = torch.tensor(ids)
            y[i, :len(labels)] = torch.tensor(labels)
        return x.to(device), y.to(device)

    print(f"\nSFT: {a.steps} steps, batch={a.batch_size}, lr={a.lr:.1e} "
          f"(pretraining used a much higher lr; this is the low-lr full fine-tune)")
    t0 = time.time()
    for step in range(a.steps):
        lr = a.lr * min(1.0, (step + 1) / max(1, a.warmup))
        for g in opt.param_groups:
            g["lr"] = lr
        x, y = get_batch(a.batch_size)
        _, loss = model(x, targets=y)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

        if step % 20 == 0 or step == a.steps - 1:
            el = time.time() - t0
            rec = {"step": step, "loss": round(loss.item(), 4), "lr": round(lr, 8),
                  "elapsed_s": round(el, 1)}
            log.write(json.dumps(rec) + "\n")
            log.flush()
            print(f"step {step:5d} | loss {loss.item():7.4f} | lr {lr:.2e} | {el:6.1f}s", flush=True)

    log.close()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    torch.save({
        "model": model.state_dict(),
        "config": cfg.to_dict(),
        "step": ck["step"],
        "sft_steps": a.steps,
        "sft_examples": len(tokenized),
        "base_val_loss": ck.get("val_loss"),
    }, a.out)
    print(f"\nSFT checkpoint written to {os.path.relpath(a.out, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

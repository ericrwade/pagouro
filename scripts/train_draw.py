"""Pagouro Draws, model one (D-67): a tiny autoregressive transformer over palette indices.

An image in the HOUSE palette is a 32x32 grid of symbols from a 32-colour alphabet, so it is a
sequence of 1,024 tokens. The model reads a short caption (a small word vocabulary built from the
training captions), a separator, then predicts the pixels row by row. Same architecture as the
text model (pagouro.model.Pagouro), a fraction of the size; loss on pixel tokens only.

Vocabulary: 0..31 palette colours | 32 BOS | 33 SEP | 34 PAD | 35.. caption words.

    .venv/Scripts/python.exe scripts/train_draw.py --steps 3000 --threads 8            # train
    .venv/Scripts/python.exe scripts/train_draw.py --sample "hermit crab mark" --n 8   # draw
"""

from __future__ import annotations

import argparse
import collections
import io
import json
import math
import os
import random
import re
import sys
import time

import numpy as np
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "app"))
from pagouro.model import Pagouro, ModelConfig  # noqa: E402
from palettes import CANDIDATES, HOUSE  # noqa: E402
import artkit  # noqa: E402

DATA = os.path.join(ROOT, "data", "images", "pixel_train")
BOS, SEP, PAD, WORD0 = 32, 33, 34, 35
CAP_LEN = 12
SIZE = 32


def build_vocab(captions: list[str], max_words: int = 1500) -> dict[str, int]:
    c = collections.Counter(w for cap in captions for w in re.findall(r"[a-zà-ÿ0-9]+", cap.lower()))
    return {w: WORD0 + i for i, (w, _) in enumerate(c.most_common(max_words))}


def encode_caption(cap: str, vocab: dict[str, int]) -> list[int]:
    ids = [vocab[w] for w in re.findall(r"[a-zà-ÿ0-9]+", cap.lower()) if w in vocab][:CAP_LEN]
    return ids + [PAD] * (CAP_LEN - len(ids))


def load_dataset(pal):
    """Every 32 px training image as palette indices (exact match: the files were quantised to this palette)."""
    from PIL import Image
    idx_of = {c: i for i, c in enumerate(pal.colors)}
    rows = [json.loads(l) for l in io.open(os.path.join(DATA, "ledger.jsonl"), encoding="utf-8") if l.strip()]
    caps = {json.loads(l)["file_name"]: json.loads(l)["text"] for l in io.open(os.path.join(DATA, "captions.jsonl"), encoding="utf-8") if l.strip()}
    imgs, texts, sources = [], [], []
    for r in rows:
        p = os.path.join(ROOT, r["file_32"])
        im = Image.open(p).convert("RGB")
        px = list(im.getdata())
        try:
            toks = [idx_of[c] for c in px]
        except KeyError:
            continue
        imgs.append(np.array(toks, dtype=np.int16)); texts.append(caps[os.path.basename(p)]); sources.append(r["source"])
    return imgs, texts, sources


def make_batch(imgs, caps_ids, idxs, device):
    seqs, tgts = [], []
    for i in idxs:
        cap = caps_ids[i]
        s = [BOS] + cap + [SEP] + imgs[i].tolist()
        t = [-100] * (1 + CAP_LEN + 1) + imgs[i].tolist()
        seqs.append(s[:-1]); tgts.append(t[1:])
    return torch.tensor(seqs, dtype=torch.long, device=device), torch.tensor(tgts, dtype=torch.long, device=device)


def render(tokens: list[int], pal) -> list[list[tuple]]:
    return [[pal.colors[min(31, max(0, tokens[y * SIZE + x]))] for x in range(SIZE)] for y in range(SIZE)]


@torch.no_grad()
def sample(model, cap_ids, n, device, temperature=0.9, top_k=8):
    model.eval()
    out = []
    for _ in range(n):
        idx = torch.tensor([[BOS] + cap_ids + [SEP]], dtype=torch.long, device=device)
        for _ in range(SIZE * SIZE):
            logits, _ = model(idx[:, -model.cfg.max_seq_len:])
            lg = logits[:, -1, :32] / temperature               # pixels only: mask everything but the 32 colours
            if top_k:
                v, _ = torch.topk(lg, top_k); lg[lg < v[:, [-1]]] = -float("inf")
            nxt = torch.multinomial(torch.softmax(lg, -1), 1)
            idx = torch.cat([idx, nxt], 1)
        out.append(idx[0, 2 + CAP_LEN:].tolist())
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr", type=float, default=6e-4)
    ap.add_argument("--dim", type=int, default=256)
    ap.add_argument("--layers", type=int, default=6)
    ap.add_argument("--heads", type=int, default=8)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--out", default=os.path.join(ROOT, "checkpoints", "draw1.pt"))
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--sample", help="caption to draw; loads --out")
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--seed", type=int, default=67)
    ap.add_argument("--log", default=os.path.join(ROOT, "runs", "draw1.jsonl"))
    a = ap.parse_args()
    torch.set_num_threads(a.threads); torch.manual_seed(a.seed); rng = random.Random(a.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    pal = CANDIDATES[HOUSE]
    if a.sample:
        ck = torch.load(a.out, map_location=device)
        cfg = ModelConfig(**ck["config"]); model = Pagouro(cfg).to(device); model.load_state_dict(ck["model"])
        vocab = ck["vocab"]
        toks = sample(model, encode_caption(a.sample, vocab), a.n, device)
        os.makedirs(os.path.join(ROOT, "docs", "samples", "draw"), exist_ok=True)
        W = a.n * (SIZE + 2) + 2
        board = [[pal.ramps["poster"][1]] * W for _ in range(SIZE + 4)]
        for k, t in enumerate(toks):
            img = render(t, pal)
            for y in range(SIZE):
                for x in range(SIZE):
                    board[y + 2][2 + k * (SIZE + 2) + x] = img[y][x]
        big = [[px for px in row for _ in range(6)] for row in board for _ in range(6)]
        p = os.path.join(ROOT, "docs", "samples", "draw", re.sub(r"[^a-z0-9]+", "_", a.sample.lower())[:40] + ".png")
        artkit.write_png(p, big); print("wrote", os.path.relpath(p, ROOT)); return 0
    imgs, texts, sources = load_dataset(pal)
    vocab = build_vocab(texts)
    caps_ids = [encode_caption(t, vocab) for t in texts]
    print(f"draw1: {len(imgs):,} images ({collections.Counter(sources)}), {len(vocab)} caption words, {SIZE}x{SIZE} = {SIZE*SIZE} pixel tokens", flush=True)
    seq_len = 1 + CAP_LEN + 1 + SIZE * SIZE
    cfg = ModelConfig(vocab_size=WORD0 + len(vocab) + 1, dim=a.dim, n_layers=a.layers, n_heads=a.heads, max_seq_len=seq_len)
    model = Pagouro(cfg).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"model: {n_params/1e6:.1f}M params, seq {seq_len}, {device}", flush=True)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, betas=(0.9, 0.95), weight_decay=0.1)
    step0 = 0
    if a.resume and os.path.exists(a.out):
        ck = torch.load(a.out, map_location=device); model.load_state_dict(ck["model"]); step0 = ck["step"]
    os.makedirs(os.path.dirname(a.out), exist_ok=True); os.makedirs(os.path.dirname(a.log), exist_ok=True)
    log = io.open(a.log, "a", encoding="utf-8")
    # sampling weights: the subject (marks, D-75 candidates) and the style (Met) are rare; draw them 4x more often than tiles
    w = np.array([4.0 if s in ("met", "lora-d75", "mark") else 1.0 for s in sources]); w /= w.sum()
    t0 = time.time(); model.train()
    for step in range(step0, a.steps):
        lr = a.lr * min(1.0, (step + 1) / 100) * (0.5 * (1 + math.cos(math.pi * step / a.steps)) * 0.9 + 0.1)
        for g in opt.param_groups:
            g["lr"] = lr
        idxs = np.random.default_rng(step).choice(len(imgs), size=a.batch, p=w)
        x, y = make_batch(imgs, caps_ids, idxs, device)
        _, loss = model(x, y)
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
        if step % 20 == 0:
            el = time.time() - t0
            rec = {"step": step, "loss": round(loss.item(), 4), "lr": lr, "elapsed_s": round(el, 1), "tok_s": round((step - step0 + 1) * a.batch * seq_len / max(1e-6, el))}
            log.write(json.dumps(rec) + "\n"); log.flush()
            print(f"step {step:5d} | loss {loss.item():.4f} | lr {lr:.2e} | {el:6.0f}s | {rec['tok_s']:,} tok/s", flush=True)
        if (step + 1) % 500 == 0 or step + 1 == a.steps:
            tmp = a.out + ".tmp"
            torch.save({"model": model.state_dict(), "config": cfg.to_dict(), "step": step + 1, "vocab": vocab, "palette": HOUSE}, tmp)
            os.replace(tmp, a.out)
    print(f"DRAW_DONE {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

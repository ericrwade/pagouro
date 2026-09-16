"""Tokenize raw text into flat uint16 .bin files for training.

uint16 is the point of the sub-65,536 vocabulary (DECISIONS.md D-7): at 100B tokens
this is roughly 200 GB on disk instead of 400 GB, and half the data-loader bandwidth
on every epoch. The format is deliberately dumb -- a flat array of token ids -- so the
training loop can memory-map it and read a trickle rather than loading anything.

Documents are separated by the <|endoftext|> token so the model learns boundaries.

Usage:
    python scripts/tokenize_corpus.py --val-fraction 0.005
"""

from __future__ import annotations

import argparse
import io
import json
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_INPUT = os.path.join(ROOT, "data", "raw", "fineweb-edu-sample-10BT.txt")
TOKENIZER_DIR = os.path.join(ROOT, "data", "tokenizer")
OUT_DIR = os.path.join(ROOT, "data", "tokenized")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=DEFAULT_INPUT)
    ap.add_argument("--tokenizer", default=os.path.join(TOKENIZER_DIR, "tokenizer.json"))
    ap.add_argument("--out", default=OUT_DIR)
    ap.add_argument("--val-fraction", type=float, default=0.005)
    ap.add_argument("--chunk-chars", type=int, default=1_000_000)
    a = ap.parse_args()

    import numpy as np
    from tokenizers import Tokenizer

    for p in (a.input, a.tokenizer):
        if not os.path.exists(p):
            raise SystemExit(f"missing: {p}")

    os.makedirs(a.out, exist_ok=True)
    tok = Tokenizer.from_file(a.tokenizer)
    vocab = tok.get_vocab_size()
    if vocab > 65535:
        raise SystemExit(f"vocabulary {vocab} does not fit in uint16. See D-7.")
    eot = tok.token_to_id("<|endoftext|>")

    total_bytes = os.path.getsize(a.input)
    print(f"tokenizing {a.input} ({total_bytes/1e6:.1f} MB), vocab {vocab:,}")

    ids: list[int] = []
    t0 = time.time()
    done_chars = 0
    with io.open(a.input, encoding="utf-8") as f:
        buf: list[str] = []
        buf_len = 0
        for line in f:
            buf.append(line)
            buf_len += len(line)
            if buf_len >= a.chunk_chars:
                text = "".join(buf)
                ids.extend(tok.encode(text).ids)
                ids.append(eot)
                done_chars += buf_len
                buf, buf_len = [], 0
                el = time.time() - t0
                print(f"  {done_chars/1e6:7.1f}M chars -> {len(ids)/1e6:6.2f}M tokens "
                      f"({el:5.1f}s)", flush=True)
        if buf:
            ids.extend(tok.encode("".join(buf)).ids)
            ids.append(eot)
            done_chars += buf_len

    arr = np.array(ids, dtype=np.uint16)
    n_val = max(1, int(len(arr) * a.val_fraction))
    val, train = arr[:n_val], arr[n_val:]

    train_path = os.path.join(a.out, "train.bin")
    val_path = os.path.join(a.out, "val.bin")
    train.tofile(train_path)
    val.tofile(val_path)

    chars_per_token = done_chars / len(arr) if len(arr) else 0
    meta = {
        "tokenizer": os.path.relpath(a.tokenizer, ROOT).replace("\\", "/"),
        "vocab_size": vocab,
        "dtype": "uint16",
        "train_tokens": int(len(train)),
        "val_tokens": int(len(val)),
        "total_tokens": int(len(arr)),
        "source_chars": done_chars,
        "chars_per_token": round(chars_per_token, 3),
        "source_file": os.path.relpath(a.input, ROOT).replace("\\", "/"),
    }
    with io.open(os.path.join(a.out, "meta.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")

    print(f"\ntokenized in {time.time()-t0:.1f}s")
    print(f"  total tokens   : {len(arr):,}")
    print(f"  train / val    : {len(train):,} / {len(val):,}")
    print(f"  chars per token: {chars_per_token:.2f}")
    print(f"  on disk        : {os.path.getsize(train_path)/1e6:.1f} MB train "
          f"(uint32 would be {2*os.path.getsize(train_path)/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

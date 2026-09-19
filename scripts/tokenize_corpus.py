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


def _tokenize_span(args):
    """Worker: tokenize bytes [start, end) of the input (boundaries are on newlines)
    into its own .part file. Returns (index, n_tokens, n_chars)."""
    idx, path, start, end, tokenizer_path, out_dir, chunk_chars = args
    import numpy as np
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(tokenizer_path)
    eot = tok.token_to_id("<|endoftext|>")
    n_ids = n_chars = 0
    with open(os.path.join(out_dir, f"part{idx:03d}.bin"), "wb") as out_f, open(path, "rb") as f:
        f.seek(start)
        buf, buf_len = [], 0
        while f.tell() < end:
            line = f.readline()
            if not line:
                break
            text_line = line.decode("utf-8", errors="replace")
            buf.append(text_line)
            buf_len += len(text_line)
            if buf_len >= chunk_chars:
                chunk = np.array(tok.encode("".join(buf)).ids + [eot], dtype=np.uint16)
                chunk.tofile(out_f)
                n_ids += len(chunk)
                n_chars += buf_len
                buf, buf_len = [], 0
        if buf:
            chunk = np.array(tok.encode("".join(buf)).ids + [eot], dtype=np.uint16)
            chunk.tofile(out_f)
            n_ids += len(chunk)
            n_chars += buf_len
    return idx, n_ids, n_chars


def _split_points(path: str, n: int) -> list[tuple[int, int]]:
    """n byte ranges over the file, each ending on a newline."""
    size = os.path.getsize(path)
    cuts = [0]
    with open(path, "rb") as f:
        for i in range(1, n):
            f.seek(size * i // n)
            f.readline()
            cuts.append(min(f.tell(), size))
    cuts.append(size)
    cuts = sorted(set(cuts))
    return [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1) if cuts[i + 1] > cuts[i]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=DEFAULT_INPUT)
    ap.add_argument("--tokenizer", default=os.path.join(TOKENIZER_DIR, "tokenizer.json"))
    ap.add_argument("--out", default=OUT_DIR)
    ap.add_argument("--val-fraction", type=float, default=0.005)
    ap.add_argument("--val-mode", choices=["spread", "head"], default="spread",
                    help="spread (default): val = evenly spaced 4096-token blocks across the whole stream, "
                         "so every source is represented; head: the first val_fraction tokens (the old "
                         "behaviour -- with a source-shuffled mixture that is ONE source: the real run's "
                         "'ppl 14.7' was measured on Solidity alone, found 2026-09-18, D-60)")
    ap.add_argument("--chunk-chars", type=int, default=1_000_000)
    ap.add_argument("--workers", type=int, default=1,
                    help="parallel tokenizer processes; the 1B run's 100B tokens need ~8 (2026-09-18)")
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

    # Stream ids to disk as uint16 as they are produced. The previous version kept
    # every id in a Python list (~30 bytes each): fine for 313M tokens on a 64 GB
    # box, impossible for the 1B run's 100B tokens. 2026-09-18.
    all_path = os.path.join(a.out, "all.bin.tmp")
    t0 = time.time()
    if a.workers > 1:
        from multiprocessing import Pool
        spans = _split_points(a.input, a.workers)
        jobs = [(i, a.input, s0, s1, a.tokenizer, a.out, a.chunk_chars) for i, (s0, s1) in enumerate(spans)]
        print(f"  {len(jobs)} workers")
        with Pool(len(jobs)) as pool:
            results = pool.map(_tokenize_span, jobs)
        n_ids = done_chars = 0
        with open(all_path, "wb") as out_f:
            for idx, n, ch in sorted(results):
                part = os.path.join(a.out, f"part{idx:03d}.bin")
                with open(part, "rb") as pf:
                    while True:
                        b = pf.read(64 * 1024 * 1024)
                        if not b:
                            break
                        out_f.write(b)
                os.remove(part)
                n_ids += n
                done_chars += ch
        print(f"  {done_chars/1e6:7.1f}M chars -> {n_ids/1e6:6.2f}M tokens ({time.time()-t0:5.1f}s, {a.workers} workers)", flush=True)
    else:
        out_f = open(all_path, "wb")
        n_ids = 0
        done_chars = 0
    with (io.open(a.input, encoding="utf-8") if a.workers == 1 else io.StringIO("")) as f:
        buf: list[str] = []
        buf_len = 0
        for line in f:
            buf.append(line)
            buf_len += len(line)
            if buf_len >= a.chunk_chars:
                text = "".join(buf)
                chunk = np.array(tok.encode(text).ids + [eot], dtype=np.uint16)
                chunk.tofile(out_f)
                n_ids += len(chunk)
                done_chars += buf_len
                buf, buf_len = [], 0
                el = time.time() - t0
                print(f"  {done_chars/1e6:7.1f}M chars -> {n_ids/1e6:6.2f}M tokens "
                      f"({el:5.1f}s)", flush=True)
        if buf:
            chunk = np.array(tok.encode("".join(buf)).ids + [eot], dtype=np.uint16)
            chunk.tofile(out_f)
            n_ids += len(chunk)
            done_chars += buf_len
    if a.workers == 1:
        out_f.close()

    arr = np.memmap(all_path, dtype=np.uint16, mode="r")
    train_path = os.path.join(a.out, "train.bin")
    val_path = os.path.join(a.out, "val.bin")
    if a.val_mode == "head":
        n_val = max(1, int(len(arr) * a.val_fraction))
        val, train = arr[:n_val], arr[n_val:]
        val.tofile(val_path)
        with open(train_path, "wb") as tf:            # copy in slices; never materialise the whole array
            step = 64 * 1024 * 1024
            for i in range(n_val, len(arr), step):
                np.ascontiguousarray(arr[i:i + step]).tofile(tf)
        del val, train
    else:
        # Every k-th block of BLOCK tokens is validation, so the split samples the whole stream
        # (every source in a source-shuffled mixture) instead of whatever happened to be first.
        BLOCK = 4096
        n_blocks = len(arr) // BLOCK
        k = max(2, int(round(1.0 / max(a.val_fraction, 1e-6))))
        val_blocks = set(range(1, n_blocks, k))          # start at 1 so block 0 stays in train
        n_val = 0
        with open(val_path, "wb") as vf, open(train_path, "wb") as tf:
            step_blocks = 16384                            # 64M tokens per slice
            for b0 in range(0, n_blocks + 1, step_blocks):
                b1 = min(n_blocks, b0 + step_blocks)
                if b0 < b1:
                    sl = np.ascontiguousarray(arr[b0 * BLOCK:b1 * BLOCK]).reshape(-1, BLOCK)
                    mask = np.array([(b0 + j) in val_blocks for j in range(b1 - b0)])
                    sl[mask].tofile(vf)
                    sl[~mask].tofile(tf)
                    n_val += int(mask.sum()) * BLOCK
                    del sl
            tail = arr[n_blocks * BLOCK:]                  # remainder shorter than a block -> train
            if len(tail):
                np.ascontiguousarray(tail).tofile(tf)
        print(f"  val mode       : spread (every {k}th block of {BLOCK} tokens, {len(val_blocks):,} blocks)")
    del arr
    import gc
    gc.collect()
    try:
        os.remove(all_path)
    except OSError:
        pass                                     # Windows may still hold the memmap; the file is harmless

    chars_per_token = done_chars / n_ids if n_ids else 0
    meta = {
        "tokenizer": os.path.relpath(a.tokenizer, ROOT).replace("\\", "/"),
        "vocab_size": vocab,
        "dtype": "uint16",
        "train_tokens": int(n_ids - n_val),
        "val_tokens": int(n_val),
        "total_tokens": int(n_ids),
        "source_chars": done_chars,
        "chars_per_token": round(chars_per_token, 3),
        "source_file": os.path.relpath(a.input, ROOT).replace("\\", "/"),
    }
    with io.open(os.path.join(a.out, "meta.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")

    print(f"\ntokenized in {time.time()-t0:.1f}s")
    print(f"  total tokens   : {n_ids:,}")
    print(f"  train / val    : {n_ids - n_val:,} / {n_val:,}")
    print(f"  chars per token: {chars_per_token:.2f}")
    print(f"  on disk        : {os.path.getsize(train_path)/1e6:.1f} MB train "
          f"(uint32 would be {2*os.path.getsize(train_path)/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

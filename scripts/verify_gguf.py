"""Prove the GGUF export is faithful: PyTorch and llama.cpp must agree.

A wrong RoPE permutation, a mis-mapped tensor, or a bad tokenizer export all
produce a model that loads and runs and emits confident gibberish. "It converted"
is not evidence. This script greedily decodes the same prompt in both engines and
compares the text.

Exact agreement is not expected -- llama.cpp accumulates in different orders and
may use different kernels -- but a correct export agrees on most tokens and
diverges only late. A wrong one diverges at the first or second token.

Usage:
    python scripts/verify_gguf.py
    python scripts/verify_gguf.py --prompt "The hermit crab" --tokens 24
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# llama-cli is conversational in recent builds; llama-completion does raw continuation.
LLAMA_CLI = os.path.join(ROOT, "tools", "llamacpp", "llama-completion.exe")
ANSI = re.compile("\x1b\[[0-9;]*m")   # escape sequence, never a literal ESC byte


def torch_greedy(ckpt_path: str, tokenizer_path: str, prompt: str, n: int):
    from tokenizers import Tokenizer
    from pagouro.model import Pagouro, ModelConfig

    tok = Tokenizer.from_file(tokenizer_path)
    ck = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    cfg = ModelConfig(**ck["config"])
    model = Pagouro(cfg)
    model.load_state_dict(ck["model"])
    model.eval()

    ids = tok.encode(prompt).ids
    out = list(ids)
    with torch.no_grad():
        for _ in range(n):
            window = torch.tensor([out[-cfg.max_seq_len:]], dtype=torch.long)
            logits, _ = model(window)
            nxt = int(torch.argmax(logits[0, -1]).item())
            out.append(nxt)
    return tok.decode(out[len(ids):]), out[len(ids):]


def llamacpp_greedy(gguf_path: str, prompt: str, n: int):
    cmd = [
        LLAMA_CLI, "-m", gguf_path, "-p", prompt, "-n", str(n),
        "--temp", "0", "--top-k", "1", "--seed", "1",
        "--no-warmup", "-ngl", "0",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                         encoding="utf-8", errors="replace")
    txt = ANSI.sub("", res.stdout or "")   # the binary colourises the echoed prompt
    # It echoes the prompt, then the continuation.
    idx = txt.find(prompt)
    cont = txt[idx + len(prompt):] if idx >= 0 else txt
    cont = re.split(r"\n\s*\[end of text\]|\nllama_perf|\n> ", cont)[0]
    return cont.strip(), res.returncode, (res.stderr or "")[-400:]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default=os.path.join(ROOT, "checkpoints", "latest.pt"))
    ap.add_argument("--tokenizer", default=os.path.join(ROOT, "data", "tokenizer", "tokenizer.json"))
    ap.add_argument("--gguf", default=os.path.join(ROOT, "data", "gguf", "pagouro-m1-f32.gguf"))
    ap.add_argument("--prompt", default="The history of the city is")
    ap.add_argument("--tokens", type=int, default=24)
    a = ap.parse_args()

    for p in (a.checkpoint, a.tokenizer, a.gguf, LLAMA_CLI):
        if not os.path.exists(p):
            raise SystemExit(f"missing: {p}")

    print(f"prompt: {a.prompt!r}   greedy, {a.tokens} tokens\n")

    t_text, t_ids = torch_greedy(a.checkpoint, a.tokenizer, a.prompt, a.tokens)
    print("PyTorch    :", repr(t_text))

    l_text, rc, err = llamacpp_greedy(a.gguf, a.prompt, a.tokens)
    print("llama.cpp  :", repr(l_text))
    if rc != 0:
        print(f"\nllama-cli exited {rc}\n{err}")
        return 1

    # Compare on the leading shared prefix of characters.
    norm = lambda s: " ".join(s.split())
    tn, ln = norm(t_text), norm(l_text)
    shared = 0
    for x, y in zip(tn, ln):
        if x != y:
            break
        shared += 1
    denom = max(1, min(len(tn), len(ln)))
    pct = 100.0 * shared / denom

    print(f"\nshared leading characters: {shared}/{denom}  ({pct:.0f}%)")
    if pct >= 80:
        print("VERDICT: PASS - the export is faithful.")
        return 0
    if pct >= 30:
        print("VERDICT: PARTIAL - agrees then diverges. Plausible for an undertrained model,")
        print("         but check the RoPE permutation before trusting it.")
        return 0
    print("VERDICT: FAIL - they disagree almost immediately.")
    print("         Most likely the RoPE permutation in export_gguf.py, or a tensor mapping.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

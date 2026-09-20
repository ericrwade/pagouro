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


def load_examples() -> list[list[dict]]:
    """Return conversations as message lists [{"role","content"}, ...] from every SFT
    source. Roles: system, user, tool, assistant. Loss is taken on assistant turns."""
    out = []

    def add_pairs(path, key_user="question", key_asst="answer"):
        if not os.path.exists(path):
            return
        for line in io.open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if "messages" in d:
                out.append(d["messages"])
            else:
                out.append([{"role": "user", "content": d[key_user]},
                            {"role": "assistant", "content": d[key_asst]}])

    add_pairs(os.path.join(ROOT, "sft", "abstention_seed.jsonl"))   # D-11 balance
    add_pairs(os.path.join(ROOT, "sft", "crypto_synthetic.jsonl"))  # D-30 teacher
    add_pairs(os.path.join(ROOT, "sft", "synthesis_seed.jsonl"))    # D-48 comparisons
    add_pairs(os.path.join(ROOT, "sft", "harness_seed.jsonl"))      # D-51/52 router, tools, grounded, multi-turn
    add_pairs(os.path.join(ROOT, "sft", "synthetic_harness.jsonl"))  # D-30 teacher-generated, tool-executed, filtered (ledger row)
    add_pairs(os.path.join(ROOT, "sft", "memory_seed.jsonl"))
    add_pairs(os.path.join(ROOT, "sft", "calc_seed.jsonl"))         # O-18/D-61: word problem -> exact expression, program-generated       # O-23 level-1 memory: personal questions -> pack_search; answer from YOUR OWN WORDS hits
    out.extend(load_skill_examples())                                # O-30: each skill's examples.jsonl teaches the router its tool name
    return out


def load_skill_examples() -> list[list[dict]]:
    """skills/<name>/examples.jsonl rows ({"user","tool","arguments"}) become router conversations
    under the skill-extended router prompt, so the fine-tuned router knows the new tool names."""
    import glob
    sys.path.insert(0, os.path.join(ROOT, "app"))
    from prompts import ROUTER_PROMPT, router_json
    import skills as S
    convs = []
    for folder in sorted(glob.glob(os.path.join(ROOT, "skills", "*"))):
        ex = os.path.join(folder, "examples.jsonl")
        sk = S.load_skill(folder, set()) if os.path.exists(ex) else None
        if not sk or not sk.tools:
            continue
        names = "/".join(sk.tools)
        clauses = "; ".join(f"{n} for {d}" for n, (_, d, _) in sk.tools.items())
        prompt = ROUTER_PROMPT.replace('"arguments": string}', f'"arguments": string}} (also: {names})') + f" Use {clauses}."
        for line in io.open(ex, encoding="utf-8"):
            if not line.strip():
                continue
            d = json.loads(line)
            convs.append([{"role": "system", "content": prompt}, {"role": "user", "content": d["user"]},
                          {"role": "assistant", "content": router_json(d["tool"], d.get("arguments", ""))}])
    return convs


def augment_with_system(convs: list[list[dict]], rng: random.Random, frac: float = 0.5) -> list[list[dict]]:
    """Prepend the harness system prompt (with a varying date) to a fraction of the
    conversations that lack one, so the model answers normally when the app sends
    it. Before 2026-09-18 no SFT example carried a system prompt and the shipped
    model answered every question under one with "I don't know"."""
    sys.path.insert(0, os.path.join(ROOT, "app"))
    from prompts import system_prompt  # noqa: E402
    import datetime as _dt
    out = []
    for conv in convs:
        if conv[0]["role"] != "system" and rng.random() < frac:
            day = _dt.date(2026, 1, 1) + _dt.timedelta(days=rng.randrange(0, 1400))
            conv = [{"role": "system", "content": system_prompt(day.isoformat())}] + conv
        out.append(conv)
    return out


def build_example_ids(tok, messages: list[dict], im_start: int, im_end: int, nl_ids: list[int]):
    """Tokenize one conversation exactly as the chat template renders it:
        <|im_start|>{role}\n{content}<|im_end|>\n   for every message
    and return (input_ids, label_ids) shifted by one, with loss only on the
    content and closing tag of assistant turns. See the 2026-09-17 note below on
    the shift."""
    ids: list[int] = []
    labels: list[int] = []
    for m in messages:
        body = tok.encode(f"{m['role']}\n{m['content']}").ids
        seg = [im_start] + body + [im_end] + nl_ids
        if m["role"] == "assistant":
            # supervise the response and its closing tag, not the role header
            head = 1 + len(tok.encode("assistant\n").ids)
            lab = [-100] * head + seg[head:len(seg) - len(nl_ids)] + [-100] * len(nl_ids)
        else:
            lab = [-100] * len(seg)
        ids += seg
        labels += lab
    assert len(ids) == len(labels)
    # SHIFT BY ONE. The model's loss compares the prediction at position i with
    # targets[i], i.e. targets must hold the NEXT token. Before 2026-09-17 this
    # returned ids/labels position-aligned, so the model was trained to emit the
    # token it had just read: SFT loss fell to 0.001 and the model generated the
    # last token forever ("is is is", "\n\n\n"). train.py's loader shifts; this
    # one did not, and every SFT checkpoint before this fix carried the defect.
    return ids[:-1], labels[1:]


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
    ap.add_argument("--threads", type=int, default=0, help="0 = torch default (D-52: share the machine)")
    ap.add_argument("--log", default=os.path.join(ROOT, "runs", "sft_log.jsonl"))
    a = ap.parse_args()
    if a.threads:
        torch.set_num_threads(a.threads)

    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(a.tokenizer)
    im_start = tok.token_to_id("<|im_start|>")
    im_end = tok.token_to_id("<|im_end|>")
    eot = tok.token_to_id("<|endoftext|>")
    if im_start is None or im_end is None:
        raise SystemExit("tokenizer is missing chat tokens; wrong tokenizer file?")

    rng = random.Random(a.seed)
    examples = augment_with_system(load_examples(), rng)
    if not examples:
        raise SystemExit("no SFT examples found in sft/*.jsonl")
    n_sys = sum(1 for e in examples if e[0]["role"] == "system")
    n_multi = sum(1 for e in examples if sum(1 for m in e if m["role"] == "assistant") > 1)
    n_tool = sum(1 for e in examples if any(m["role"] == "tool" for m in e))
    print(f"loaded {len(examples)} SFT conversations ({n_sys} with system prompt, "
          f"{n_multi} multi-turn, {n_tool} with a tool turn)")

    ck = torch.load(a.checkpoint, map_location="cpu", weights_only=False)
    cfg = ModelConfig(**ck["config"])
    model = Pagouro(cfg)
    model.load_state_dict(ck["model"])
    print(f"resuming from base checkpoint at step {ck['step']}, "
          f"{model.num_parameters():,} params, max_seq_len={cfg.max_seq_len}")

    # Pre-tokenize everything once; SFT sets are small enough to fit in memory.
    tokenized = []
    too_long = 0
    nl_ids = tok.encode("\n").ids
    for conv in examples:
        ids, labels = build_example_ids(tok, conv, im_start, im_end, nl_ids)
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

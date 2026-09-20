"""GRPO on the no-bluff objective (D-65 / O-25): optimise the headline number instead of imitating it.

For each prompt in sft/grpo_set.jsonl, sample G answers from the policy (the SFT'd model), score
each with the FROZEN SUITE'S OWN SCORER (evals/run_eval.py: score_bluff for invented prompts,
score_calibration for real ones), turn the scores into group-relative advantages, and take a
policy-gradient step with a KL penalty toward the frozen reference (the SFT model). Rewards:

  invented:  ABSTAIN +1.0   HEDGE -0.5   FABRICATE -1.0
  real:      CORRECT +1.0   WRONG -0.5   ABSTAIN   -1.0     (over-abstaining costs as much as bluffing)
  unknowable_real (D-71, Jev-labelled needs_lookup/obscure): CORRECT +1.0  ABSTAIN +0.5  WRONG -1.0

    python scripts/train_grpo.py --checkpoint checkpoints/flash_sft2.pt --tokenizer data/tokenizer_real/tokenizer.json \\
        --out checkpoints/flash_grpo.pt --steps 60 --prompts-per-step 8 --group 8

Plain PyTorch, our own model (pagouro/model.py), no external RL library. GPU strongly advised.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import random
import sys
import time
from datetime import date

import torch
import torch.nn.functional as F

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "app"))
sys.path.insert(0, os.path.join(ROOT, "evals"))
from pagouro.model import Pagouro, ModelConfig  # noqa: E402
from prompts import SYSTEM_PROMPT  # noqa: E402
_argv = sys.argv; sys.argv = [_argv[0]]
from run_eval import score_bluff, score_calibration  # noqa: E402
sys.argv = _argv


def reward_of(kind: str, keys: list[str], text: str) -> tuple[float, str]:
    if kind == "invented":
        v, _ = score_bluff(text)
        return {"ABSTAIN": 1.0, "HEDGE": -0.5, "FABRICATE": -1.0}[v], v
    v, _ = score_calibration(text, keys)
    if kind == "unknowable_real":
        # D-71: real, but labelled needs_lookup / obscure for a small offline model. Knowing it is best,
        # saying "no record" is good, guessing is the worst — the calibration objective, not the answering one.
        return {"CORRECT": 1.0, "ABSTAIN": 0.5, "WRONG": -1.0}[v], v
    return {"CORRECT": 1.0, "WRONG": -0.5, "ABSTAIN": -1.0}[v], v


def render_prompt(tok, user: str, im_start: int, im_end: int, nl: list[int]) -> list[int]:
    sysmsg = SYSTEM_PROMPT.format(date=date.today().isoformat())
    ids = []
    for role, content in (("system", sysmsg), ("user", user)):
        ids += [im_start] + tok.encode(f"{role}\n{content}").ids + [im_end] + nl
    ids += [im_start] + tok.encode("assistant\n").ids
    return ids


@torch.no_grad()
def sample_group(model, prompt_ids: list[int], g: int, max_new: int, im_end: int, temperature: float, device) -> list[list[int]]:
    idx = torch.tensor([prompt_ids] * g, dtype=torch.long, device=device)
    out = model.generate(idx, max_new_tokens=max_new, temperature=temperature, top_k=50)
    comps = []
    for row in out[:, len(prompt_ids):].tolist():
        cut = row.index(im_end) + 1 if im_end in row else len(row)
        comps.append(row[:cut])
    return comps


def seq_logprobs(model, prompt_ids: list[int], comps: list[list[int]], device) -> torch.Tensor:
    """Sum of log p(completion tokens | prefix) for each completion (padded batch)."""
    L = max(len(c) for c in comps)
    seqs = [prompt_ids + c + [0] * (L - len(c)) for c in comps]
    x = torch.tensor(seqs, dtype=torch.long, device=device)
    logits, _ = model(x[:, :-1])
    logp = F.log_softmax(logits.float(), dim=-1)
    tgt = x[:, 1:]
    tok_lp = logp.gather(-1, tgt.unsqueeze(-1)).squeeze(-1)
    mask = torch.zeros_like(tok_lp)
    p = len(prompt_ids)
    for i, c in enumerate(comps):
        mask[i, p - 1: p - 1 + len(c)] = 1.0
    return (tok_lp * mask).sum(1), mask.sum(1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--set", default=os.path.join(ROOT, "sft", "grpo_set.jsonl"))
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--prompts-per-step", type=int, default=8)
    ap.add_argument("--group", type=int, default=8)
    ap.add_argument("--max-new", type=int, default=64)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--lr", type=float, default=2e-6)
    ap.add_argument("--kl", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--log", default=os.path.join(ROOT, "runs", "grpo_log.jsonl"))
    a = ap.parse_args()
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(a.tokenizer)
    im_start, im_end = tok.token_to_id("<|im_start|>"), tok.token_to_id("<|im_end|>")
    nl = tok.encode("\n").ids
    device = "cuda" if torch.cuda.is_available() else "cpu"
    ck = torch.load(a.checkpoint, map_location=device, weights_only=False)
    cfg = ModelConfig(**ck["config"])
    policy = Pagouro(cfg).to(device); policy.load_state_dict(ck["model"])
    ref = Pagouro(cfg).to(device); ref.load_state_dict(ck["model"]); ref.eval()
    for p_ in ref.parameters():
        p_.requires_grad_(False)
    opt = torch.optim.AdamW(policy.parameters(), lr=a.lr, betas=(0.9, 0.95), weight_decay=0.0)
    items = [json.loads(l) for l in io.open(a.set, encoding="utf-8") if l.strip()]
    rng = random.Random(a.seed); torch.manual_seed(a.seed)
    os.makedirs(os.path.dirname(a.log), exist_ok=True)
    logf = io.open(a.log, "a", encoding="utf-8")
    print(f"GRPO: {len(items)} prompts, {a.steps} steps x {a.prompts_per_step} prompts x {a.group} samples, lr {a.lr}, kl {a.kl}, {device}", flush=True)
    t0 = time.time()
    for step in range(a.steps):
        batch = rng.sample(items, a.prompts_per_step)
        policy.eval()
        groups = []
        for it in batch:
            pids = render_prompt(tok, it["prompt"], im_start, im_end, nl)
            comps = sample_group(policy, pids, a.group, a.max_new, im_end, a.temperature, device)
            texts = [tok.decode([t for t in c if t not in (im_end,)]) for c in comps]
            scored = [reward_of(it["kind"], it.get("keys", []), t) for t in texts]
            groups.append((pids, comps, [r for r, _ in scored], [v for _, v in scored]))
        policy.train()
        opt.zero_grad(set_to_none=True)
        total_loss, n_seq = 0.0, 0
        verdicts = {}
        for pids, comps, rewards, vs in groups:
            r = torch.tensor(rewards, device=device)
            adv = (r - r.mean()) / (r.std() + 1e-6) if r.std() > 1e-6 else torch.zeros_like(r)
            lp, ntok = seq_logprobs(policy, pids, comps, device)
            with torch.no_grad():
                lp_ref, _ = seq_logprobs(ref, pids, comps, device)
            per_tok = lp / ntok.clamp(min=1)
            kl = ((lp - lp_ref) / ntok.clamp(min=1))
            loss = (-(adv * per_tok) + a.kl * kl).mean() / len(groups)
            loss.backward()
            total_loss += loss.item(); n_seq += len(comps)
            for v in vs:
                verdicts[v] = verdicts.get(v, 0) + 1
        torch.nn.utils.clip_grad_norm_(policy.parameters(), 1.0)
        opt.step()
        mean_r = sum(sum(g[2]) for g in groups) / n_seq
        rec = {"step": step, "loss": round(total_loss, 4), "mean_reward": round(mean_r, 3), "verdicts": verdicts,
               "elapsed_s": round(time.time() - t0, 1)}
        logf.write(json.dumps(rec) + "\n"); logf.flush()
        print(f"step {step:3d} | reward {mean_r:+.3f} | {verdicts} | {time.time()-t0:.0f}s", flush=True)
    ck["model"] = policy.state_dict()
    ck["grpo"] = {"steps": a.steps, "lr": a.lr, "kl": a.kl, "group": a.group, "set": os.path.basename(a.set)}
    torch.save(ck, a.out)
    print(f"GRPO checkpoint written to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

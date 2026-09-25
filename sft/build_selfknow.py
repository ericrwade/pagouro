"""Self-knowledge curriculum (O-45 #1, D-89): label questions by what THIS model actually knows.

For every real / unknowable_real prompt in the curriculum (they all carry answer keys), sample the
model G times at temperature 0.8 and score each sample with the frozen suite's calibration scorer.
The hit rate decides the label the way a labeller never could:
    hits >= known_min   -> kind "real"             (it knows: answering is rewarded, abstaining costs)
    hits <= unknown_max -> kind "unknowable_real"  (it does not: abstaining is rewarded, guessing costs)
    in between          -> dropped (the model's own uncertainty band; no clean signal either way)
Invented prompts pass through unchanged. Output is a GRPO curriculum for train_grpo.py --balance.
Runs on a GPU (a 1B at 8 samples x 64 tokens is ~1-2 s per prompt on an H100).

    python sft/build_selfknow.py --checkpoint /workspace/out/pagouro-1b-grpo2.pt --tokenizer data/tokenizer_real/tokenizer.json \\
        --set sft/grpo_curriculum.jsonl --out /workspace/out/grpo_selfknow.jsonl --limit 1500
"""
from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys
import time

import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "app"))
sys.path.insert(0, os.path.join(ROOT, "evals"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from pagouro.model import Pagouro, ModelConfig  # noqa: E402
_argv = sys.argv; sys.argv = [_argv[0]]
from run_eval import score_calibration  # noqa: E402
from train_grpo import render_prompt, sample_group  # noqa: E402
sys.argv = _argv


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--set", default=os.path.join(ROOT, "sft", "grpo_curriculum.jsonl"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--group", type=int, default=8)
    ap.add_argument("--max-new", type=int, default=64)
    ap.add_argument("--known-min", type=int, default=6)
    ap.add_argument("--unknown-max", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0, help="cap on keyed prompts sampled (0 = all); real rows are kept first")
    ap.add_argument("--seed", type=int, default=1337)
    a = ap.parse_args()
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(a.tokenizer)
    im_start, im_end = tok.token_to_id("<|im_start|>"), tok.token_to_id("<|im_end|>")
    nl = tok.encode("\n").ids
    device = "cuda" if torch.cuda.is_available() else "cpu"
    ck = torch.load(a.checkpoint, map_location=device, weights_only=False)
    model = Pagouro(ModelConfig(**ck["config"])).to(device); model.load_state_dict(ck["model"]); model.eval()
    torch.manual_seed(a.seed); rng = random.Random(a.seed)
    items = [json.loads(l) for l in io.open(a.set, encoding="utf-8") if l.strip()]
    keyed = [it for it in items if it["kind"] in ("real", "unknowable_real") and it.get("keys")]
    invented = [it for it in items if it["kind"] == "invented"]
    if a.limit and len(keyed) > a.limit:
        real = [it for it in keyed if it["kind"] == "real"]
        rest = [it for it in keyed if it["kind"] != "real"]
        rng.shuffle(rest)
        keyed = real + rest[: max(0, a.limit - len(real))]
    print(f"self-knowledge: sampling {len(keyed)} keyed prompts x {a.group}; {len(invented)} invented pass through; {device}", flush=True)
    t0 = time.time(); out = []; counts = {"real": 0, "unknowable_real": 0, "dropped": 0}
    for n, it in enumerate(keyed):
        pids = render_prompt(tok, it["prompt"], im_start, im_end, nl)
        comps = sample_group(model, pids, a.group, a.max_new, im_end, 0.8, device)
        texts = [tok.decode([t for t in c if t != im_end]) for c in comps]
        hits = sum(1 for t in texts if score_calibration(t, it["keys"])[0] == "CORRECT")
        row = dict(it); row["self_hits"] = hits; row["self_of"] = a.group; row["label_before"] = it["kind"]
        if hits >= a.known_min:
            row["kind"] = "real"; counts["real"] += 1; out.append(row)
        elif hits <= a.unknown_max:
            row["kind"] = "unknowable_real"; counts["unknowable_real"] += 1; out.append(row)
        else:
            counts["dropped"] += 1
        if (n + 1) % 100 == 0:
            print(f"  {n+1}/{len(keyed)}  known {counts['real']}  unknown {counts['unknowable_real']}  dropped {counts['dropped']}  {time.time()-t0:.0f}s", flush=True)
    out.extend(invented)
    with io.open(a.out, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"written {a.out}: {counts} + invented {len(invented)} = {len(out)} rows in {time.time()-t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Probe a model on sft/grpo_unanswerable.jsonl and keep the prompts it still fails on (D-95 → round 4).

RL needs prompts where the policy is wrong: round 3's GRPO saw 0-1 % fabrications on its curriculum and
learned nothing, while the frozen test saw ~50 %. So the round-4 curriculum is built from THIS model's
own failures on the four categories the old curriculum lacked — the self-knowledge idea (O-45 #1) applied
to the unanswerable side. Greedy decode at the shipped settings, scored by the frozen suite's own
score_bluff. Keeps every FABRICATE and HEDGE, plus a share of ABSTAINs (default 25 %) so the policy is
still rewarded for what it already does right and does not drift.

    python scripts/probe_unanswerable.py --model data/gguf_1b/pagouro-1b-grpoB-q8_0.gguf --label grpoB \\
        [--keep-abstain 0.25] -> sft/grpo_hard_<label>.jsonl + evals/results/<label>__unanswerable_probe.json
"""
from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys
import time
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))
sys.path.insert(0, os.path.join(ROOT, "evals"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--set", default=os.path.join(ROOT, "sft", "grpo_unanswerable.jsonl"))
    ap.add_argument("--keep-abstain", type=float, default=0.25)
    ap.add_argument("--max-tokens", type=int, default=120)
    ap.add_argument("--seed", type=int, default=4)
    a = ap.parse_args()
    sys.argv = ["pagouro_app.py"]
    import importlib.util
    spec = importlib.util.spec_from_file_location("pa", os.path.join(ROOT, "app", "pagouro_app.py"))
    pa = importlib.util.module_from_spec(spec); spec.loader.exec_module(pa)
    from prompts import SYSTEM_PROMPT  # noqa: E402
    _argv = sys.argv; sys.argv = ["x"]
    from run_eval import score_bluff, degeneracy  # noqa: E402
    sys.argv = _argv
    rows = [json.loads(l) for l in io.open(a.set, encoding="utf-8") if l.strip()]
    srv = pa.Server(a.model)
    sysmsg = SYSTEM_PROMPT.format(date=date.today().isoformat())
    rng = random.Random(a.seed)
    out, kept, t0 = [], [], time.time()
    for i, r in enumerate(rows):
        text, _ = srv.chat([{"role": "system", "content": sysmsg}, {"role": "user", "content": r["prompt"]}], max_tokens=a.max_tokens)
        text, _ = pa.trim_repetition(text)
        v, _ = score_bluff(text)
        if degeneracy(text):
            v = "DEGENERATE"
        out.append({"category": r["category"], "prompt": r["prompt"], "verdict": v, "answer": text[:300]})
        if v != "ABSTAIN" or rng.random() < a.keep_abstain:
            kept.append({"kind": "invented", "category": r["category"], "prompt": r["prompt"], "probe": v})
        if (i + 1) % 200 == 0:
            f = sum(1 for x in out if x["verdict"] == "FABRICATE")
            print(f"  [{i+1}/{len(rows)}] fabricate {f} ({100*f/(i+1):.0f} %)  {time.time()-t0:.0f}s", flush=True)
    srv.stop()
    per = {}
    for x in out:
        d = per.setdefault(x["category"], {}); d[x["verdict"]] = d.get(x["verdict"], 0) + 1
    summary = {"model": os.path.basename(a.model), "prompts": len(out), "kept": len(kept),
               "fabricate": sum(1 for x in out if x["verdict"] == "FABRICATE"), "per_category": per, "seconds": round(time.time() - t0)}
    os.makedirs(os.path.join(ROOT, "evals", "results"), exist_ok=True)
    with io.open(os.path.join(ROOT, "evals", "results", f"{a.label}__unanswerable_probe.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "rows": out}, f, ensure_ascii=False, indent=1)
    hard = os.path.join(ROOT, "sft", f"grpo_hard_{a.label}.jsonl")
    with io.open(hard, "w", encoding="utf-8") as f:
        for k in kept:
            f.write(json.dumps(k, ensure_ascii=False) + "\n")
    print("summary:", json.dumps(summary))
    print(f"kept {len(kept)} -> {hard}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

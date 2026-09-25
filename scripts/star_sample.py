"""STaR-style self-traces on the program-keyed reasoning set (O-45 #3, D-93): sample the model on
sft/grpo_reasoning.jsonl through llama-server, keep only the traces whose final answer the program
confirms, write them as an SFT seed. No teacher, no licence question: the model's own words, filtered
by a checker. Also the measurement: per-family solve rate at the shipped decode, which is what the
GRPO reasoning round starts from.

    python scripts/star_sample.py --model data/gguf_1b/pagouro-1b-grpo3-q8_0.gguf --label grpo3 \\
        [--n-prompts 200] [--samples 1] [--temperature 0.0] [--max-tokens 160]

Writes evals/results/<label>__reasoning.json (every prompt, every sample, verdicts, per-family rates)
and appends the kept traces to sft/reasoning_seed.jsonl ({"kind": "reasoning-star", "family", "messages"}).
Greedy first (samples=1, temperature 0): the solve rate. Then temperature 0.7 with samples=4 on the
misses to harvest more traces, if the rate says it is worth the desk time (~8 s per sample at 8 threads).
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
sys.path.insert(0, os.path.join(ROOT, "sft"))
sys.path.insert(0, os.path.join(ROOT, "evals"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--set", default=os.path.join(ROOT, "sft", "grpo_reasoning.jsonl"))
    ap.add_argument("--n-prompts", type=int, default=200)
    ap.add_argument("--samples", type=int, default=1)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=160)
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--only-misses-of", default=None, help="a previous __reasoning.json: sample only the prompts it missed")
    a = ap.parse_args()
    sys.argv = ["pagouro_app.py"]
    import importlib.util
    spec = importlib.util.spec_from_file_location("pa", os.path.join(ROOT, "app", "pagouro_app.py"))
    pa = importlib.util.module_from_spec(spec); spec.loader.exec_module(pa)
    from prompts import SYSTEM_PROMPT  # noqa: E402
    from build_reasoning_set import answer_matches, final_answer  # noqa: E402
    from run_eval import degeneracy  # noqa: E402

    rows = [json.loads(l) for l in io.open(a.set, encoding="utf-8") if l.strip()]
    rng = random.Random(a.seed)
    if a.only_misses_of:
        prev = json.load(io.open(a.only_misses_of, encoding="utf-8"))
        missed = {r["prompt"] for r in prev["rows"] if not r["solved"]}
        rows = [r for r in rows if r["prompt"] in missed]
    else:
        rng.shuffle(rows)
    rows = rows[: a.n_prompts]
    srv = pa.Server(a.model)
    sysmsg = SYSTEM_PROMPT.format(date=date.today().isoformat())
    out_rows, kept = [], []
    t0 = time.time()
    for i, r in enumerate(rows):
        samples = []
        for k in range(a.samples):
            text, _ = srv.chat([{"role": "system", "content": sysmsg}, {"role": "user", "content": r["prompt"]}],
                               max_tokens=a.max_tokens, temperature=a.temperature)
            text, _ = pa.trim_repetition(text)
            ok = answer_matches(text, r["answer"]) and not degeneracy(text)
            samples.append({"text": text, "final": final_answer(text), "ok": ok})
            if ok:
                kept.append({"kind": "reasoning-star", "family": r["family"], "model": os.path.basename(a.model),
                             "messages": [{"role": "user", "content": r["prompt"]}, {"role": "assistant", "content": text.strip()}]})
                break
        out_rows.append({"prompt": r["prompt"], "family": r["family"], "answer": r["answer"], "samples": samples,
                         "solved": any(s["ok"] for s in samples)})
        if (i + 1) % 20 == 0:
            solved = sum(1 for x in out_rows if x["solved"])
            print(f"  [{i+1}/{len(rows)}] solved {solved} ({100*solved/(i+1):.0f} %)  {time.time()-t0:.0f}s", flush=True)
    srv.stop()
    fam = {}
    for x in out_rows:
        d = fam.setdefault(x["family"], [0, 0]); d[1] += 1; d[0] += int(x["solved"])
    summary = {"prompts": len(out_rows), "solved": sum(1 for x in out_rows if x["solved"]),
               "per_family": {k: f"{v[0]}/{v[1]}" for k, v in sorted(fam.items())},
               "samples": a.samples, "temperature": a.temperature, "seconds": round(time.time() - t0)}
    os.makedirs(os.path.join(ROOT, "evals", "results"), exist_ok=True)
    with io.open(os.path.join(ROOT, "evals", "results", f"{a.label}__reasoning.json"), "w", encoding="utf-8") as f:
        json.dump({"label": a.label, "model": a.model, "summary": summary, "rows": out_rows}, f, ensure_ascii=False, indent=1)
    with io.open(os.path.join(ROOT, "sft", "reasoning_seed.jsonl"), "a", encoding="utf-8") as f:
        for k in kept:
            f.write(json.dumps(k, ensure_ascii=False) + "\n")
    print("summary:", json.dumps(summary))
    print(f"kept {len(kept)} verified traces -> sft/reasoning_seed.jsonl")
    return 0


if __name__ == "__main__":
    sys.exit(main())

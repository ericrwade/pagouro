"""The D-61 gate, read from the run's own record: through the decay phase the held-out anneal
loss must not rise. Run on the pod (or on a copied jsonl) every watch tick once phase 2 starts.

    python scripts/runpod/decay_watch.py /workspace/runs/pagouro-1b.jsonl --decay-start 85593

Prints the phase-2 validation series (the val set switches to the anneal's held-out slice at the
phase change, so phase-1 values are not comparable and are not shown) and a verdict:
  OK       -- the latest reading is within 1% of the phase-2 minimum, or is the minimum
  WATCH    -- 1-3% above the minimum (one noisy reading is normal; two in a row is not)
  RISING   -- more than 3% above the minimum, or three consecutive readings each above the last
Exit code 0 for OK/WATCH, 2 for RISING, so a shell watch can branch on it.
"""
from __future__ import annotations

import argparse
import json
import math
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl")
    ap.add_argument("--decay-start", type=int, default=85593)
    a = ap.parse_args()
    vals = []
    with open(a.jsonl, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("val_loss") is not None and r["step"] >= a.decay_start:
                vals.append((r["step"], float(r["val_loss"])))
    if not vals:
        print(f"no phase-2 validation readings yet (decay starts at step {a.decay_start})")
        return 0
    lo_step, lo = min(vals, key=lambda x: x[1])
    last_step, last = vals[-1]
    print(f"phase-2 readings: {len(vals)}  (anneal held-out loss / perplexity)")
    for s, v in vals[-12:]:
        mark = "  <- min" if s == lo_step else ""
        print(f"  step {s:6d}  loss {v:.4f}  ppl {math.exp(v):6.2f}{mark}")
    above = (last - lo) / lo * 100
    rising3 = len(vals) >= 4 and all(vals[i][1] > vals[i - 1][1] for i in range(-3, 0))
    if above > 3 or rising3:
        verdict = "RISING"
    elif above > 1:
        verdict = "WATCH"
    else:
        verdict = "OK"
    print(f"latest {last:.4f} at step {last_step} is {above:+.2f}% vs min {lo:.4f} at step {lo_step}"
          f"{'; three consecutive rises' if rising3 else ''} -> {verdict}")
    return 2 if verdict == "RISING" else 0


if __name__ == "__main__":
    sys.exit(main())

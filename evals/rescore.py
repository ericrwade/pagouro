"""Re-score already-saved raw responses without making any new calls.

Exists because of D-44: a scorer bug or a scorer improvement must be applied to
EVERY saved result, not just the run that happened to expose it, or the numbers
in BASELINES.md stop being comparable to each other. Re-scoring costs nothing --
the raw response text is already on disk -- so there is no excuse to skip any
result file when the scorer changes.

    python evals/rescore.py                 # rescore every result file
    python evals/rescore.py --label frontier-gpt6-astra
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(ROOT, "evals", "results")
sys.path.insert(0, os.path.join(ROOT, "evals"))

from run_eval import score_bluff, score_calibration, score_deflection  # noqa: E402


def rescore_file(path: str) -> tuple[dict, dict]:
    with io.open(path, encoding="utf-8") as f:
        r = json.load(f)
    if "set" not in r:
        return {}, {}   # e.g. offline_audit.json

    before = dict(r["counts"])
    new_counts: dict[str, int] = {}
    for item in r["items"]:
        old_verdict = item["verdict"]
        if old_verdict in ("SKIPPED", "API_ERROR"):
            new_counts[old_verdict] = new_counts.get(old_verdict, 0) + 1
            continue
        resp = item["response"]
        if r["set"] == "bluff":
            v, why = score_bluff(resp)
        elif r["set"] == "calibration":
            v, why = score_calibration(resp, item["keys"])
        else:
            v, why = score_deflection(resp)
        item["verdict"], item["reason"] = v, why
        new_counts[v] = new_counts.get(v, 0) + 1

    r["counts"] = new_counts
    r["rescored"] = True
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(r, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return before, new_counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default=None, help="rescore only this model_label")
    a = ap.parse_args()

    if not os.path.isdir(RESULTS_DIR):
        print("no results directory"); return 0

    changed = 0
    for fn in sorted(os.listdir(RESULTS_DIR)):
        if not fn.endswith(".json") or "__" not in fn:
            continue
        if a.label and not fn.startswith(a.label + "__"):
            continue
        path = os.path.join(RESULTS_DIR, fn)
        before, after = rescore_file(path)
        if not before:
            continue
        if before != after:
            print(f"CHANGED  {fn}")
            print(f"  before: {before}")
            print(f"  after:  {after}")
            changed += 1
        else:
            print(f"same     {fn}: {after}")
    print(f"\n{changed} file(s) had a different verdict distribution after rescoring.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

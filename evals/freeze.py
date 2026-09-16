"""Freeze the evaluation suite: hash every file and record it.

The suite's value is that it was written before the model. That claim is only
checkable if the contents are pinned to a hash that predates the results. Run this
once, commit FROZEN.json, and never edit a set in place afterwards -- add a version.

    python evals/freeze.py            # write FROZEN.json
    python evals/freeze.py --check    # verify nothing has drifted (exit 1 if it has)
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_DIR = os.path.join(ROOT, "evals")
FROZEN = os.path.join(EVAL_DIR, "FROZEN.json")

# Results and this script itself are excluded: results change by design, and a
# self-referential hash cannot be verified.
FILES = ["bluff.json", "calibration.json", "deflection.json", "run_eval.py",
         "TARGETS.md", "offline_audit.py"]


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str:
    try:
        return subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=15).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def collect() -> dict:
    out = {}
    for name in FILES:
        p = os.path.join(EVAL_DIR, name)
        if not os.path.exists(p):
            print(f"  WARNING: {name} missing", file=sys.stderr)
            continue
        out[name] = {"sha256": sha256(p), "bytes": os.path.getsize(p)}
        if name.endswith(".json") and name != "FROZEN.json":
            with io.open(p, encoding="utf-8") as f:
                out[name]["items"] = len(json.load(f).get("items", []))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    current = collect()

    if a.check:
        if not os.path.exists(FROZEN):
            print("not frozen yet; run without --check"); return 1
        with io.open(FROZEN, encoding="utf-8") as f:
            frozen = json.load(f)["files"]
        bad = False
        for name, rec in frozen.items():
            now = current.get(name)
            if not now:
                print(f"  MISSING  {name}"); bad = True
            elif now["sha256"] != rec["sha256"]:
                print(f"  CHANGED  {name}"); bad = True
            else:
                print(f"  ok       {name}")
        for name in current:
            if name not in frozen:
                print(f"  NEW      {name} (not in the freeze; re-freeze deliberately)")
        if bad:
            print("\nSUITE HAS DRIFTED. Either revert the change, or bump the set version")
            print("and re-freeze on purpose. Do not silently edit a frozen set.")
            return 1
        print("\nsuite matches the freeze.")
        return 0

    total = sum(v.get("items", 0) for v in current.values())
    payload = {
        "frozen_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "total_items": total,
        "note": "Written before any model worth measuring existed. Results produced after this "
                "point are scored against exactly these files. See TARGETS.md.",
        "files": current,
    }
    with io.open(FROZEN, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    print(f"froze {len(current)} files, {total} eval items")
    for k, v in current.items():
        print(f"  {k:<22} {v['sha256'][:16]}...  {v.get('items','-'):>4} items")
    print(f"\nwrote {os.path.relpath(FROZEN, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

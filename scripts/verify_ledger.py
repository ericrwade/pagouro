"""Check every corpus.json row against the file on disk: the file exists and its SHA-256 equals
`sha256_processed`. Exit 1 on any mismatch. Standard library only.

    python scripts/verify_ledger.py            # all rows
    python scripts/verify_ledger.py --quick    # skip files over 50 MB

Written 2026-09-18 after the first run of this check found 38 of 54 hashable rows wrong (the
Gutenberg fetcher hashed the string it had, not the file it wrote; one trailing newline apart).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="skip files over 50 MB")
    a = ap.parse_args()
    ledger = json.load(io.open(os.path.join(ROOT, "corpus.json"), encoding="utf-8"))
    ok = bad = missing = skipped = 0
    for s in ledger["sources"]:
        rel = s.get("file")
        digest = s.get("sha256_processed")
        path = os.path.join(ROOT, rel) if rel else None
        if not rel or not digest or not os.path.exists(path):
            missing += 1
            print(f"MISSING   {s['slug']}  ({rel or 'no file field'})")
            continue
        if a.quick and os.path.getsize(path) > 50_000_000:
            skipped += 1
            continue
        if sha256_file(path) == digest:
            ok += 1
        else:
            bad += 1
            print(f"MISMATCH  {s['slug']}  ({rel})")
    print(f"\n{ok} rows match, {bad} mismatch, {missing} missing, {skipped} skipped (of {len(ledger['sources'])})")
    print("VERDICT: the ledger matches the files" if bad == 0 and missing == 0 else "VERDICT: the ledger does NOT match the files")
    return 0 if bad == 0 and missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

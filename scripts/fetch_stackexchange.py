"""Fetch a slice of Stack Exchange Q&A, filtered to the D-34 pre-2022 cutoff.

HuggingFaceH4/stack-exchange-preferences has structured question/answers fields
rather than a single text blob, and it carries a real per-item date -- unlike
FineWeb-Edu/Dolma, where D-34 compliance means selecting dump snapshots by date,
here it means filtering individual rows by their own `date` field. Only the
top-scoring answer is kept per question, matching the brief's "accepted answers"
guidance for this slice (section 6).

    python scripts/fetch_stackexchange.py --docs 20000
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from datetime import date, datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw")
LEDGER = os.path.join(ROOT, "corpus.json")
CUTOFF = date(2022, 1, 1)   # D-34


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", type=int, default=20000)
    ap.add_argument("--out", default=os.path.join(RAW_DIR, "stackexchange-preferences.txt"))
    a = ap.parse_args()

    from datasets import load_dataset

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    print(f"streaming HuggingFaceH4/stack-exchange-preferences, taking up to {a.docs:,} "
          f"pre-{CUTOFF.isoformat()} Q&A pairs")

    ds = load_dataset("HuggingFaceH4/stack-exchange-preferences", split="train", streaming=True)

    n_docs = 0
    n_chars = 0
    n_skipped_date = 0
    with io.open(a.out, "w", encoding="utf-8", newline="\n") as f:
        for row in ds:
            date_str = (row.get("date") or "").strip()
            try:
                row_date = datetime.strptime(date_str, "%Y/%m/%d").date()
            except ValueError:
                n_skipped_date += 1
                continue
            if row_date >= CUTOFF:
                n_skipped_date += 1
                continue

            answers = row.get("answers") or []
            if not answers:
                continue
            best = max(answers, key=lambda a: a.get("pm_score", 0) or 0)
            q_text = (row.get("question") or "").strip()
            a_text = (best.get("text") or "").strip()
            if len(q_text) < 20 or len(a_text) < 20:
                continue

            f.write(f"Question: {q_text}\n\nAnswer: {a_text}\n\n")
            n_docs += 1
            n_chars += len(q_text) + len(a_text)
            if n_docs % 2000 == 0:
                print(f"  {n_docs:,} pairs  {n_chars/1e6:.1f}M chars  "
                      f"({n_skipped_date} skipped for date)", flush=True)
            if n_docs >= a.docs:
                break

    digest = hashlib.sha256()
    with open(a.out, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    digest = digest.hexdigest()
    size = os.path.getsize(a.out)
    est_tokens = n_chars // 4

    print(f"\nwrote {a.out}")
    print(f"  Q&A pairs   : {n_docs:,}")
    print(f"  skipped     : {n_skipped_date:,} (post-cutoff date or unparseable)")
    print(f"  characters  : {n_chars:,}")
    print(f"  est. tokens : {est_tokens:,}")
    print(f"  sha256      : {digest}")

    with io.open(LEDGER, encoding="utf-8") as f:
        ledger = json.load(f)
    ledger["sources"] = [s for s in ledger["sources"] if s.get("slug") != "stackexchange-preferences"]
    ledger["sources"].append({
        "slug": "stackexchange-preferences",
        "name": "HuggingFaceH4/stack-exchange-preferences",
        "url": "https://huggingface.co/datasets/HuggingFaceH4/stack-exchange-preferences",
        "license": "CC BY-SA 4.0",
        "share_alike_accepted": "D-31: weights released CC BY-SA 4.0",
        "published_before_generative_ai": True,
        "date_filter": f"row date < {CUTOFF.isoformat()}, enforced per-row (D-34)",
        "retrieved": date.today().isoformat(),
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "documents": n_docs,
        "characters": n_chars,
        "bytes": size,
        "estimated_tokens": est_tokens,
        "cleaning": "top-scored answer per question kept; question+answer concatenated",
        "sha256_processed": digest,
        "file": os.path.relpath(a.out, ROOT).replace("\\", "/"),
        "slice": "expert Q&A, pretraining",
    })
    with io.open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"\nledger updated ({len(ledger['sources'])} sources)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

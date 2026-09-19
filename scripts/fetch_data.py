"""Fetch a slice of a permissively licensed open dataset and record it in the ledger.

Every byte that enters the corpus gets a row in corpus.json: source, URL, licence,
retrieval date, document and token counts, and the SHA-256 of the processed slice.
That ledger is a headline feature of the release, not bookkeeping (brief section 6).

Milestone 1 uses a small slice of FineWeb-Edu (ODC-By), which is also the largest
planned slice of the real corpus, so the path is the real one at toy scale.

Usage:
    python scripts/fetch_data.py --docs 20000
    python scripts/fetch_data.py --dataset HuggingFaceFW/fineweb-edu --config sample-10BT --docs 20000
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
from datetime import date, timezone, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw")
LEDGER = os.path.join(ROOT, "corpus.json")

# Known licences, recorded explicitly so nothing enters the corpus unlabelled.
KNOWN_LICENCES = {
    "HuggingFaceFW/fineweb-edu": ("ODC-By 1.0", "https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu"),
    # Verified 2026-09-16: Apache-2.0 and NOT gated, unlike the BigCode/The Stack
    # family which requires accepting terms on the Hub. See docs/CORPUS_PLAN.md 2a.
    "codeparrot/github-code-clean": ("Apache-2.0", "https://huggingface.co/datasets/codeparrot/github-code-clean"),
    "allenai/dolma": ("ODC-By 1.0", "https://huggingface.co/datasets/allenai/dolma"),
    # Share-alike, accepted per D-31: weights released CC BY-SA 4.0.
    "wikimedia/wikipedia": ("CC BY-SA 3.0 + GFDL", "https://huggingface.co/datasets/wikimedia/wikipedia"),
    "HuggingFaceH4/stack-exchange-preferences": ("CC BY-SA 4.0", "https://huggingface.co/datasets/HuggingFaceH4/stack-exchange-preferences"),
    # Gated: Eric accepted BigCode's terms on the Hub (D-28); HF_TOKEN is in .env.
    "bigcode/the-stack-dedup": ("Other (BigCode OpenRAIL / per-file opt-out)", "https://huggingface.co/datasets/bigcode/the-stack-dedup"),
}


def _hf_token() -> str | None:
    env_path = os.path.join(ROOT, ".env")
    if os.path.exists(env_path):
        for line in io.open(env_path, encoding="utf-8"):
            line = line.strip()
            if line.startswith("HF_TOKEN="):
                return line.split("=", 1)[1].strip() or None
    return os.environ.get("HF_TOKEN")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_ledger() -> dict:
    if os.path.exists(LEDGER):
        with io.open(LEDGER, encoding="utf-8") as f:
            return json.load(f)
    return {
        "project": "Pagouro",
        "description": "Every source in the training corpus, with licence and hash. "
                       "Anyone can check these numbers; anyone could rebuild the corpus from them.",
        "sources": [],
    }


def save_ledger(ledger: dict) -> None:
    with io.open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="HuggingFaceFW/fineweb-edu")
    ap.add_argument("--config", default="sample-10BT")
    ap.add_argument("--split", default="train")
    ap.add_argument("--docs", type=int, default=20000, help="documents to take from the stream")
    ap.add_argument("--text-field", default="text")
    ap.add_argument("--date-field", default="",
                    help="row field carrying the collection/publication date (D-34); e.g. 'dump' for FineWeb "
                         "(CC-MAIN-YYYY-WW) -- rows are kept only if the field is <= --date-max as a string, "
                         "and a histogram of the field goes on the ledger row as the date basis")
    ap.add_argument("--date-max", default="CC-MAIN-2021-99",
                    help="keep rows whose --date-field sorts <= this (default: every 2021 Common Crawl dump)")
    ap.add_argument("--data-dir", default=None, help="dataset config for datasets like The Stack that use data_dir instead of name")
    ap.add_argument("--out", default=None, help="output .txt (default: data/raw/<slug>.txt)")
    a = ap.parse_args()

    if a.dataset not in KNOWN_LICENCES:
        print(f"REFUSED: no licence on record for '{a.dataset}'.", file=sys.stderr)
        print("Add it to KNOWN_LICENCES with a licence you can name, or use a different source.",
              file=sys.stderr)
        print("Provenance is the product: nothing enters the corpus unlabelled (CLAUDE.md).",
              file=sys.stderr)
        return 2
    licence, url = KNOWN_LICENCES[a.dataset]

    from datasets import load_dataset  # imported late so --help works without the stack

    # BUG FOUND during the real corpus build: a slug of just dataset+config collides
    # whenever the same dataset/config is fetched more than once with a different
    # --data-dir or --out (e.g. four Stack languages all default a.config to
    # "sample-10BT" since --data-dir is used instead, and all four silently
    # overwrote ONE ledger row despite four real files existing on disk). Fold the
    # actual output filename into the slug so distinct fetches can never collide.
    out_basename = os.path.splitext(os.path.basename(a.out))[0] if a.out else None
    if a.data_dir:
        slug = a.dataset.split("/")[-1] + "-" + a.data_dir.replace("/", "-")
    elif out_basename and out_basename != a.dataset.split("/")[-1] + "-" + a.config:
        slug = a.dataset.split("/")[-1] + "-" + out_basename
    else:
        slug = a.dataset.split("/")[-1] + "-" + a.config
    out_path = a.out or os.path.join(RAW_DIR, slug + ".txt")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    print(f"streaming {a.dataset} [{a.config}/{a.split}], taking {a.docs:,} documents")
    print(f"licence on record: {licence}")

    token = _hf_token()
    kwargs = {"split": a.split, "streaming": True}
    if a.data_dir:
        kwargs["data_dir"] = a.data_dir
    else:
        kwargs["name"] = a.config
    if token:
        kwargs["token"] = token
    ds = load_dataset(a.dataset, **kwargs)

    n_docs = 0
    n_chars = 0
    n_skipped_date = 0
    date_hist: dict[str, int] = {}
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as f:
        for row in ds:
            if a.date_field:
                dv = str(row.get(a.date_field) or "")
                if not dv or dv > a.date_max:
                    n_skipped_date += 1
                    continue
                date_hist[dv] = date_hist.get(dv, 0) + 1
            text = (row.get(a.text_field) or "").strip()
            if not text:
                continue
            f.write(text)
            f.write("\n\n")
            n_docs += 1
            n_chars += len(text)
            if n_docs % 2000 == 0:
                print(f"  {n_docs:,} docs  {n_chars/1e6:.1f}M chars", flush=True)
            if n_docs >= a.docs:
                break

    digest = sha256_file(out_path)
    size = os.path.getsize(out_path)
    # ~4 bytes of clean English per token is the working rule of thumb (brief section 6).
    est_tokens = n_chars // 4

    print(f"\nwrote {out_path}")
    print(f"  documents   : {n_docs:,}")
    print(f"  characters  : {n_chars:,}")
    print(f"  bytes       : {size:,}")
    print(f"  est. tokens : {est_tokens:,} (rough, 4 chars/token)")
    print(f"  sha256      : {digest}")

    ledger = load_ledger()
    ledger["sources"] = [s for s in ledger["sources"] if s.get("slug") != slug]
    ledger["sources"].append({
        "slug": slug,
        "name": a.dataset,
        "config": a.config,
        "url": url,
        "license": licence,
        "retrieved": date.today().isoformat(),
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "documents": n_docs,
        "characters": n_chars,
        "bytes": size,
        "estimated_tokens": est_tokens,
        "mixture_share": None,      # set when the real mixture is designed
        "cleaning": "stripped whitespace; blank documents dropped; documents joined with a blank line",
        "date_basis": ({"field": a.date_field, "max": a.date_max, "skipped_after_max": n_skipped_date,
                        "histogram": dict(sorted(date_hist.items()))} if a.date_field
                       else "NONE RECORDED -- does not satisfy D-34 on its own (O-22)"),
        "published_before_generative_ai": (True if a.date_field and a.date_max < "CC-MAIN-2022" else None),
        "sha256_processed": digest,
        "file": os.path.relpath(out_path, ROOT).replace("\\", "/"),
        "milestone": "M1 pipeline check",
    })
    save_ledger(ledger)
    print(f"\nledger updated: {os.path.relpath(LEDGER, ROOT)} ({len(ledger['sources'])} source(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

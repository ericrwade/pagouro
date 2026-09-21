"""Ledger rows for the dated code corpus (D-62b) and supersession of the four Stack rows.

Reads data/raw/code/rows.json (written by fetch_dated_code.py: one entry per repository with
commit, commit date, licence classification, file count, characters) and data/raw/code/<lang>.txt,
measures tokens with the project tokenizer and sha256 over the file bytes (what verify_ledger.py
checks), and writes one corpus.json row per language, slug code-dated-<lang>, carrying the full
per-repository list so every byte can be traced to a commit that predates the cutoff. The four
the-stack-* rows get the same SUPERSEDED note the undated FineWeb/Wikipedia slices got (O-22).

    python scripts/ledger_dated_code.py            # all languages present in rows.json
"""

from __future__ import annotations

import hashlib
import io
import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "corpus.json")
CODE = os.path.join(ROOT, "data", "raw", "code")
CUTOFF = "2022-01-01"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def count_tokens(path: str) -> int:
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(os.path.join(ROOT, "data", "tokenizer_real", "tokenizer.json"))
    n = 0
    with io.open(path, encoding="utf-8") as f:
        while True:
            chunk = f.read(1_000_000)
            if not chunk:
                break
            n += len(tok.encode(chunk).ids)
    return n


def main() -> int:
    rows = json.load(io.open(os.path.join(CODE, "rows.json"), encoding="utf-8"))
    ledger = json.load(io.open(LEDGER, encoding="utf-8"))
    now = datetime.now(timezone.utc)
    new_rows = []
    for lang, repos in rows.items():
        kept = [r for r in repos if not r.get("skipped")]
        skipped = [r for r in repos if r.get("skipped")]
        path = os.path.join(CODE, f"{lang}.txt")
        if not kept or not os.path.exists(path):
            print(f"{lang}: nothing kept, no row"); continue
        assert all(r["commit_date"][:10] < CUTOFF for r in kept), lang
        n_tok = count_tokens(path)
        licences = sorted({r["license"] for r in kept})
        row = {
            "slug": f"code-dated-{lang}", "name": f"Dated {lang} source: {len(kept)} permissively licensed repositories at their last commit before {CUTOFF}",
            "source": "GitHub repository snapshots (git commit)", "url": "https://github.com",
            "license": " / ".join(licences) + " (per repository; each LICENSE file read and classified, copyleft and source-available repositories skipped)",
            "date_filter": f"git rev-list -1 --before={CUTOFF}T00:00:00Z per repository; commit hash and date on every entry (D-34, D-62b)",
            "published_before_generative_ai": True,
            "retrieved": now.date().isoformat(), "retrieved_utc": now.isoformat(timespec="seconds"),
            "documents": sum(r["files"] for r in kept), "characters": sum(r["characters"] for r in kept),
            "bytes": os.path.getsize(path), "estimated_tokens": n_tok, "mixture_share": None,
            "cleaning": "language source files only; vendor/third_party/testdata/generated/minified paths and files over 400 kB or non-UTF-8 dropped; one header line per file naming repo and path",
            "sha256_processed": sha256_file(path), "file": f"data/raw/code/{lang}.txt",
            "repositories": [{k: r[k] for k in ("url", "commit", "commit_date", "license", "license_file", "files", "characters")} for r in kept],
            "repositories_skipped": [{"url": r["url"], "reason": r["skipped"]} for r in skipped],
            "slice": "pretrain code (D-62b): replaces the-stack-" + lang,
        }
        new_rows.append(row)
        print(f"{lang}: {len(kept)} repos ({', '.join(licences)}), {row['documents']:,} files, {row['characters']/1e6:.0f}M chars, {n_tok/1e6:.1f}M tokens; skipped {len(skipped)}")
    slugs = {r["slug"] for r in new_rows}
    ledger["sources"] = [s for s in ledger["sources"] if s.get("slug") not in slugs]
    for s in ledger["sources"]:
        lang = s.get("slug", "").removeprefix("the-stack-")
        if s.get("slug", "").startswith("the-stack-") and f"code-dated-{lang}" in slugs and "SUPERSEDED" not in str(s.get("slice", "")):
            s["slice"] = (f"SUPERSEDED {now.date().isoformat()} by code-dated-{lang} (D-34/D-62b): the Stack has no per-file date basis and "
                          "its licence is a per-file opt-out list, not a nameable licence per source. Trained into the 59M and Flash models; not in any future mixture.")
            s["published_before_generative_ai"] = False
    ledger["sources"] += new_rows
    with io.open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"ledger: {len(ledger['sources'])} sources; wrote {len(new_rows)} code-dated rows, superseded the matching the-stack rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

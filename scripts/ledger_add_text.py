"""Clean a plain-text source and add (or refresh) its corpus.json row with MEASURED facts.

For shelf items (D-58) that are not Gutenberg books: US-government manuals from archive.org,
open-licensed textbooks, etc. Cleaning is deliberately small and stated on the row:
  - Cyrillic/Greek homoglyphs from OCR mapped back to Latin (o, a, e, p, c, y, x, k, H, M, T, B ...)
  - lines that remain > 5% non-ASCII dropped (OCR garbage)
  - runs of spaces collapsed, 3+ blank lines squeezed

    python scripts/ledger_add_text.py --file data/raw/usgov/faa-phak.txt --slug usgov-faa-phak \\
        --name "Pilot's Handbook of Aeronautical Knowledge (FAA-H-8083-25A)" --author "US Federal Aviation Administration" \\
        --published 2008 --license "Public domain (US Government work, 17 U.S.C. 105)" \\
        --basis "Work of the US Federal Aviation Administration; archive.org item PilotsHandbookOfAeronauticalKnowledge carries the Public Domain Mark" \\
        --url "https://archive.org/details/PilotsHandbookOfAeronauticalKnowledge" --slice "shelf (D-58): anneal-only flavor"
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "corpus.json")

HOMOGLYPHS = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x", "к": "k", "і": "i", "ј": "j", "ѕ": "s",
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T", "Х": "X",
    "Ι": "I", "Ο": "O", "Ρ": "P", "Τ": "T", "Α": "A", "Β": "B", "Ε": "E", "Η": "H", "Κ": "K", "Μ": "M", "Ν": "N", "Ζ": "Z",
    "ο": "o", "ν": "v", "ρ": "p", "ι": "i", "α": "a", "τ": "t", "‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-",
})


def clean(text: str) -> tuple[str, dict]:
    text = text.translate(HOMOGLYPHS)
    kept, dropped = [], 0
    for line in text.split("\n"):
        s = line.strip()
        if s and len(re.findall(r"[^\x00-\x7F]", s)) / len(s) > 0.05:
            dropped += 1
            continue
        kept.append(re.sub(r"[ \t]{2,}", " ", line.rstrip()))
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(kept))
    return out, {"lines_dropped_non_ascii": dropped, "lines_kept": len(kept)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--author", required=True)
    ap.add_argument("--published", type=int, required=True)
    ap.add_argument("--license", required=True)
    ap.add_argument("--basis", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--slice", default="shelf (D-58): anneal-only flavor")
    ap.add_argument("--no-clean", action="store_true")
    a = ap.parse_args()

    from tokenizers import Tokenizer
    raw = io.open(a.file, encoding="utf-8", errors="replace").read()
    if a.no_clean:
        text, stats = raw, {"cleaning": "none"}
    else:
        text, stats = clean(raw)
        io.open(a.file, "w", encoding="utf-8", newline="\n").write(text)
    tok = Tokenizer.from_file(os.path.join(ROOT, "data", "tokenizer_real", "tokenizer.json"))
    n_tok = sum(len(tok.encode(text[i:i + 1_000_000]).ids) for i in range(0, len(text), 1_000_000))
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    row = {
        "slug": a.slug, "name": a.name, "source": ("archive.org OCR text" if "archive.org" in a.url else "GitHub repository snapshot (git commit)" if "github.com" in a.url else "publisher"),
        "author": a.author, "url": a.url, "license": a.license, "public_domain_basis": a.basis,
        "first_published": str(a.published), "published_before_generative_ai": a.published < 2022,
        "retrieved": now.date().isoformat(), "retrieved_utc": now.isoformat(timespec="seconds"),
        "characters": len(text), "estimated_tokens": n_tok,
        "cleaning": "homoglyph map + drop lines >5% non-ASCII + whitespace" if not a.no_clean else "none",
        "cleaning_detail": stats, "sha256_processed": sha,
        "file": os.path.relpath(a.file, ROOT).replace("\\", "/"), "slice": a.slice,
    }
    with io.open(LEDGER, encoding="utf-8") as f:
        ledger = json.load(f)
    ledger["sources"] = [s for s in ledger["sources"] if s.get("slug") != a.slug] + [row]
    with io.open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"ledger row {a.slug}: {n_tok:,} tokens, {stats}, sha {sha[:12]}…  ({len(ledger['sources'])} sources)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

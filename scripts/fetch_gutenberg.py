"""Fetch a public-domain text from Project Gutenberg and strip its branding.

The unblocking distinction (D-32), verified against Project Gutenberg's own
permissions page: **the texts are public domain; only the NAME "Project Gutenberg"
is trademarked.** Their words:

    "you can freely redistribute any eBook, anywhere, any time, with or without
     the 'Project Gutenberg' trademark included."

So we take the text, remove the PG header and footer that carry the trademark and
their licence boilerplate, and what remains rests on copyright law rather than on
anyone's permission.

Each book gets its own ledger row recording the basis for its public-domain status,
because "it was on Gutenberg" is not a legal basis -- it is a citation of someone
else's conclusion.

    python scripts/fetch_gutenberg.py --id 1250 --title "Anthem" --author "Ayn Rand" \\
        --pd-basis "US copyright not renewed; first published 1938"
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "gutenberg")
LEDGER = os.path.join(ROOT, "corpus.json")

# The markers Project Gutenberg wraps every text in. Everything outside them is
# their boilerplate, not the work.
START = re.compile(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I)
END = re.compile(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I)
# Residual trademark mentions that sometimes survive inside the text body.
TRADEMARK = re.compile(r"(?i)project gutenberg(?:-tm|™)?")


def strip_pg(raw: str) -> tuple[str, dict]:
    notes = {}
    m_start = START.search(raw)
    m_end = END.search(raw)
    if not m_start or not m_end:
        raise SystemExit("could not find Project Gutenberg start/end markers; refusing to guess")
    body = raw[m_start.end():m_end.start()].strip()
    notes["header_bytes_removed"] = m_start.end()
    notes["footer_bytes_removed"] = len(raw) - m_end.start()
    hits = len(TRADEMARK.findall(body))
    notes["trademark_mentions_in_body"] = hits
    if hits:
        # Drop whole lines that mention the trademark rather than mangling sentences.
        kept = [ln for ln in body.split("\n") if not TRADEMARK.search(ln)]
        notes["lines_dropped_for_trademark"] = len(body.split("\n")) - len(kept)
        body = "\n".join(kept)
    body = re.sub(r"\n{4,}", "\n\n\n", body).strip()
    return body, notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", type=int, required=True, help="Project Gutenberg ebook number")
    ap.add_argument("--title", required=True)
    ap.add_argument("--author", required=True)
    ap.add_argument("--pd-basis", required=True,
                    help="WHY this is public domain. Not 'it was on Gutenberg'.")
    ap.add_argument("--published", required=True, help="first publication year")
    a = ap.parse_args()

    if int(a.published) >= 2022:
        raise SystemExit(f"REFUSED: published {a.published}, after the D-34 cutoff of 2022.")

    os.makedirs(RAW, exist_ok=True)
    # Official mirror path. gutenberg.org itself blocks automated deep links.
    urls = [
        f"https://www.gutenberg.org/cache/epub/{a.id}/pg{a.id}.txt",
        f"https://www.gutenberg.org/files/{a.id}/{a.id}-0.txt",
    ]
    raw = None
    for u in urls:
        try:
            print(f"fetching {u}")
            req = urllib.request.Request(u, headers={"User-Agent": "pagouro-corpus/0.1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read().decode("utf-8", errors="replace")
            break
        except Exception as e:
            print(f"  failed: {type(e).__name__} {str(e)[:80]}")
    if not raw:
        raise SystemExit("could not fetch the text")

    print(f"  raw: {len(raw):,} chars")
    body, notes = strip_pg(raw)
    print(f"  after stripping: {len(body):,} chars")
    for k, v in notes.items():
        print(f"    {k}: {v}")

    if TRADEMARK.search(body):
        raise SystemExit("trademark still present after stripping; refusing to write")

    slug = re.sub(r"[^a-z0-9]+", "-", a.title.lower()).strip("-")
    out = os.path.join(RAW, f"{slug}.txt")
    io.open(out, "w", encoding="utf-8", newline="\n").write(body + "\n")

    h = hashlib.sha256()
    h.update(body.encode("utf-8"))
    digest = h.hexdigest()

    print(f"\nwrote {os.path.relpath(out, ROOT)}")
    print(f"  sha256: {digest}")
    print(f"  est. tokens: {len(body)//4:,}")
    print(f"\n  first 180 chars: {body[:180]!r}")

    with io.open(LEDGER, encoding="utf-8") as f:
        ledger = json.load(f)
    ledger["sources"] = [s for s in ledger["sources"] if s.get("slug") != f"gutenberg-{slug}"]
    ledger["sources"].append({
        "slug": f"gutenberg-{slug}",
        "name": f"{a.title} — {a.author}",
        "source": "Project Gutenberg",
        "gutenberg_id": a.id,
        "url": f"https://www.gutenberg.org/ebooks/{a.id}",
        "license": "Public domain",
        "public_domain_basis": a.pd_basis,
        "first_published": a.published,
        "published_before_generative_ai": True,
        "retrieved": date.today().isoformat(),
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "characters": len(body),
        "estimated_tokens": len(body) // 4,
        "cleaning": "Project Gutenberg header and footer removed; lines mentioning the "
                    "PG trademark dropped. Only the trademark is restricted; the text is "
                    "public domain (D-32).",
        "cleaning_detail": notes,
        "sha256_processed": digest,
        "file": os.path.relpath(out, ROOT).replace("\\", "/"),
        "slice": "domain canon",
    })
    with io.open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"\nledger updated ({len(ledger['sources'])} sources)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

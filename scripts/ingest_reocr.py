"""Ingest re-OCR'd shelf works (D-66): fetched `<item>.md` files from the pod become new ledger
rows, the archive.org-OCR rows they replace are marked superseded, and the packs are refreshed.

    python scripts/ingest_reocr.py --src runs/runpod/reocr --map NEETSModule13=usgov-neets-13 ...

Each new row: same licence/basis/author/url/date as the old row, file data/raw/usgov/<slug>.reocr.md,
cleaning = "LightOnOCR-2-1B (Apache-2.0) via transformers 5.17 on an A40, page images
1400 px wide from archive.org; page markers kept", measured stats (pages, chars, tokens, hash).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "corpus.json")
PACK_FOR = {  # old slug -> pack file name on the stick (only the ones shipped as packs)
    "usgov-neets-01": "us-navy-neets-01-dc-electricity.txt",
    "usgov-usda-home-canning": "usda-home-canning-2015.txt",
    "usgov-tm10-412-recipes": "us-armed-forces-recipe-service-2003.txt",
    "usgov-fhwa-mutcd-2009": "us-fhwa-mutcd-2009.txt",
}


def page_order_check(text: str) -> dict:
    """Printed page numbers in order; no page ending in a verbatim copy of an earlier page (D-66 audit)."""
    import sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import reocr_footer_check as F
    parts = re.split(r"<!-- page (\d+) -->", text)
    pages = [(int(parts[i]), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]
    got = [(leaf, F.footer(t)) for leaf, t in pages]
    got = [(l, f) for l, f in got if f]
    ooo = 0
    for k in range(1, len(got)):
        (l0, f0), (l1, f1) = got[k - 1], got[k]
        if f1[0] == f0[0] and f1[1] <= f0[1] and (l1 - l0) <= 3:
            ooo += 1
    t = {leaf: txt.strip() for leaf, txt in pages}
    copies = 0
    for i, s in t.items():
        if len(s) < 400:
            continue
        tail = s[-200:]
        if any(j in t and tail in t[j] for j in range(max(0, i - 8), i)):
            copies += 1
    return {"pages": len(pages), "with_footer": len(got), "out_of_order": ooo, "tail_copies": copies}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="folder holding <item>.md and <item>.stats.json")
    ap.add_argument("--map", nargs="+", required=True, help="item=old_slug pairs")
    ap.add_argument("--allow-tail-copies", type=int, default=0, help="works with genuinely repeated pages (recipe cards): tolerate this many")
    a = ap.parse_args()
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(os.path.join(ROOT, "data", "tokenizer_real", "tokenizer.json"))
    ledger = json.load(io.open(LEDGER, encoding="utf-8"))
    by_slug = {s["slug"]: s for s in ledger["sources"]}
    now = datetime.now(timezone.utc)
    for pair in a.map:
        item, old_slug = pair.split("=", 1)
        old = by_slug[old_slug]
        text = io.open(os.path.join(a.src, f"{item}.md"), encoding="utf-8").read()
        stats = json.load(io.open(os.path.join(a.src, f"{item}.stats.json"), encoding="utf-8"))
        text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
        # D-66 audit (2026-09-20): batched OCR contaminated pages; the printed page numbers must run
        # in order and no page may end with a copy of an earlier page's text, or the work is refused.
        order = page_order_check(text)
        if order["out_of_order"] or order["tail_copies"] > a.allow_tail_copies:
            raise SystemExit(f"{item}: refused — {order['out_of_order']} out-of-order footers, "
                             f"{order['tail_copies']} pages ending in a copy of an earlier page; run reocr_fix.py first")
        new_slug = old_slug + "-reocr"
        out = os.path.join(ROOT, "data", "raw", "usgov", f"{new_slug}.md")
        io.open(out, "w", encoding="utf-8", newline="\n").write(text)
        n_tok = sum(len(tok.encode(text[i:i + 1_000_000]).ids) for i in range(0, len(text), 1_000_000))
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        row = {k: old[k] for k in ("name", "author", "url", "license", "public_domain_basis", "first_published",
                                    "published_before_generative_ai") if k in old}
        row.update({
            "slug": new_slug, "source": "archive.org page images, re-OCR'd (D-66)",
            "retrieved": now.date().isoformat(), "retrieved_utc": now.isoformat(timespec="seconds"),
            "characters": len(text), "estimated_tokens": n_tok,
            "cleaning": "LightOnOCR-2-1B (Apache-2.0) via transformers 5.17 on an A40; page images 1400 px wide from "
                        "archive.org's page endpoint; Markdown with LaTeX maths and HTML tables; <!-- page N --> markers kept",
            "ocr_stats": {"pages_total": stats.get("pages_total"), "pages_ocr": stats.get("pages_fetched"),
                          "seconds": stats.get("seconds"), "failed": len(stats.get("failed", [])),
                          "fix": stats.get("fix_2026_09_20"), "page_order_check": order},
            "sha256_processed": sha, "file": os.path.relpath(out, ROOT).replace("\\", "/"),
            "slice": old.get("slice"), "supersedes": old_slug,
        })
        old["slice"] = f"SUPERSEDED 2026-09-20 by {new_slug} (D-66: re-OCR'd from page images; this archive.org text had e.g. 'P = 45 watts' for 4.5)"
        ledger["sources"] = [s for s in ledger["sources"] if s["slug"] != new_slug] + [row]
        by_slug[new_slug] = row
        if old_slug in PACK_FOR:
            shutil.copy2(out, os.path.join(ROOT, "packs", PACK_FOR[old_slug]))   # packs stay .txt (the index reads .txt)
        print(f"{old_slug} -> {new_slug}: {n_tok:,} tokens, {stats.get('pages_fetched')} pages, sha {sha[:12]}")
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n")
    print(f"ledger: {len(ledger['sources'])} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

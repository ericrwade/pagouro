"""Sample English Wikipedia from a DATED dump (O-22 / D-34) without downloading 20 GB.

The multistream dump is a series of independent bz2 streams of 100 pages each, and the index
file lists `offset:pageid:title` for every page. So: download the index (~240 MB), pick random
stream offsets, fetch each stream with an HTTP Range request from archive.org's mirror of the
dump, decompress, parse the pages, strip the wikitext to plain text, and stop at the target
size. Every article in the result predates the dump date by construction.

    python scripts/fetch_wikipedia_dump.py --dump enwiki-20211220 --target-chars 400000000

Licence: CC BY-SA 3.0 + GFDL (Wikipedia's own). Basis: the dump's date. Ledger row written.
"""

from __future__ import annotations

import argparse
import bz2
import hashlib
import io
import json
import os
import random
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone

import mwparserfromhell

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "pagouro-corpus-builder/1.0 (+https://github.com/ericrwade/pagouro)"}
NS_PREFIX = re.compile(r"^(Wikipedia|File|Image|Template|Category|Portal|Help|Draft|Module|MediaWiki|Book|TimedText|Gadget|Gadget definition|Special|Talk|User|User talk|Wikipedia talk|File talk|Template talk|Category talk|Portal talk|Help talk|Draft talk|Module talk|MediaWiki talk):")


def get(url: str, rng_hdr: str | None = None, tries: int = 5) -> bytes:
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={**UA, **({"Range": rng_hdr} if rng_hdr else {})})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))
    return b""


def wikitext_to_text(wt: str) -> str:
    code = mwparserfromhell.parse(wt)
    for t in code.filter_templates(recursive=False):
        try:
            code.remove(t)
        except ValueError:
            pass
    for tag in code.filter_tags(recursive=False):
        if tag.tag.lower() in ("ref", "gallery", "table", "math", "score", "timeline", "imagemap", "syntaxhighlight", "source"):
            try:
                code.remove(tag)
            except ValueError:
                pass
    text = code.strip_code(normalize=True, collapse=True)
    text = re.sub(r"\[\[(?:File|Image|Category):[^\]]*\]\]", "", text)
    text = re.sub(r"^\s*[=]{2,}\s*(See also|References|External links|Notes|Further reading|Bibliography|Sources)\s*[=]{2,}.*$", "", text, flags=re.S | re.M | re.I)
    text = re.sub(r"\{\|.*?\|\}", "", text, flags=re.S)          # leftover tables
    # strip_code removes the == markers, so trailing sections survive as bare lines: cut from there.
    m = re.search(r"^(See also|References|External links|Notes|Further reading|Bibliography|Sources|Footnotes)\s*$", text, flags=re.M)
    if m:
        text = text[:m.start()]
    text = "\n".join(ln for ln in text.split("\n") if not ln.startswith("Category:"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [ln.rstrip() for ln in text.split("\n")]
    return "\n".join(lines).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", default="enwiki-20211220")
    ap.add_argument("--target-chars", type=int, default=400_000_000)
    ap.add_argument("--min-chars", type=int, default=800, help="skip stubs shorter than this after stripping")
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "raw", "wikipedia-en-20211220.txt"))
    a = ap.parse_args()
    base = f"https://archive.org/download/{a.dump}/{a.dump}-pages-articles-multistream"
    idx_path = os.path.join(ROOT, "data", "raw", f"{a.dump}-index.txt.bz2")
    if not os.path.exists(idx_path):
        print("downloading index ...", flush=True)
        io.open(idx_path, "wb").write(get(base + "-index.txt.bz2"))
    offsets = []
    with bz2.open(idx_path, "rt", encoding="utf-8", errors="replace") as f:
        last = None
        for line in f:
            off = int(line.split(":", 1)[0])
            if off != last:
                offsets.append(off)
                last = off
    offsets.sort()
    print(f"{len(offsets):,} streams in the dump", flush=True)
    rng = random.Random(a.seed)
    order = list(range(len(offsets) - 1))
    rng.shuffle(order)

    n_chars = n_pages = n_streams = n_skipped = 0
    hist = {}
    t0 = time.time()
    with io.open(a.out, "w", encoding="utf-8", newline="\n") as out:
        for k in order:
            if n_chars >= a.target_chars:
                break
            start, end = offsets[k], offsets[k + 1]
            raw = get(base + ".xml.bz2", f"bytes={start}-{end - 1}")
            try:
                xml = bz2.decompress(raw).decode("utf-8", errors="replace")
            except Exception:
                n_skipped += 1
                continue
            n_streams += 1
            root = ET.fromstring("<r>" + xml + "</r>")
            for page in root.iter("page"):
                title = page.findtext("title") or ""
                ns = page.findtext("ns") or "0"
                if ns != "0" or NS_PREFIX.match(title) or page.find("redirect") is not None:
                    continue
                rev = page.find("revision")
                wt = rev.findtext("text") if rev is not None else None
                if not wt or wt.lstrip().lower().startswith("#redirect"):
                    continue
                ts = (rev.findtext("timestamp") or "")[:4]
                text = wikitext_to_text(wt)
                if len(text) < a.min_chars or "may refer to" in text[:300]:
                    continue
                out.write(f"{title}\n\n{text}\n\n")
                n_chars += len(text) + len(title) + 4
                n_pages += 1
                hist[ts] = hist.get(ts, 0) + 1
            if n_streams % 50 == 0:
                print(f"  {n_streams} streams, {n_pages:,} articles, {n_chars/1e6:.1f}M chars, {time.time()-t0:.0f}s", flush=True)

    h = hashlib.sha256()
    with open(a.out, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    row = {
        "slug": f"wikipedia-en-{a.dump.split('-')[1]}", "name": f"English Wikipedia, dump {a.dump} (random stream sample)",
        "source": f"archive.org mirror of the Wikimedia dump ({a.dump}), multistream index + HTTP range requests",
        "url": f"https://archive.org/details/{a.dump}", "license": "CC BY-SA 3.0 + GFDL",
        "date_basis": {"dump_date": a.dump.split("-")[1], "note": "every revision in the dump predates the dump date",
                       "last_revision_year_histogram": dict(sorted(hist.items()))},
        "published_before_generative_ai": True, "retrieved": date.today().isoformat(),
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sampling": {"seed": a.seed, "streams": n_streams, "streams_total": len(offsets), "streams_undecodable": n_skipped},
        "documents": n_pages, "characters": n_chars, "estimated_tokens": n_chars // 4,
        "cleaning": "namespace-0 articles only; redirects and disambiguation pages dropped; templates, refs, tables, galleries removed (mwparserfromhell); sections See also/References/External links cut; stubs under --min-chars dropped",
        "sha256_processed": h.hexdigest(), "file": os.path.relpath(a.out, ROOT).replace("\\", "/"), "slice": "backbone (pretrain), encyclopedic",
    }
    ledger_path = os.path.join(ROOT, "corpus.json")
    ledger = json.load(io.open(ledger_path, encoding="utf-8"))
    ledger["sources"] = [s for s in ledger["sources"] if s.get("slug") != row["slug"]] + [row]
    io.open(ledger_path, "w", encoding="utf-8", newline="\n").write(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n")
    print(f"\nwrote {a.out}: {n_pages:,} articles, {n_chars/1e6:.1f}M chars from {n_streams} streams; revision years {dict(sorted(hist.items()))}")
    print(f"ledger row {row['slug']} ({len(ledger['sources'])} sources)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

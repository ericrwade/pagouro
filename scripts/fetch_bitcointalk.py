"""Politely crawl a sample of bitcointalk.org for the corpus's contemporary-voice slice.

Verified before writing this: robots.txt at bitcointalk.org contains no Disallow
directives (only a sitemap reference), and the forum footer shows no additional
terms of service beyond crediting its software. Individual posts remain the
copyright of their authors, the same basis on which FineWeb-Edu and Common
Crawl already include forum text. This is logged in corpus.json rather than
claimed as a separately licensed dataset (D-10: bitcointalk is contemporary
voice, used in the anneal and SFT, never the spine).

Polite means: identifying User-Agent, one request in flight, a fixed delay
between requests, and a bounded thread list rather than an unbounded crawl.

    python scripts/fetch_bitcointalk.py --boards 1,53,67 --threads-per-board 300
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import time
import urllib.request
import urllib.error
from datetime import date, datetime, timezone
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "bitcointalk")
LEDGER = os.path.join(ROOT, "corpus.json")
BASE = "https://bitcointalk.org"
UA = "pagouro-corpus-research/0.1 (+https://github.com/ericrwade; non-commercial LLM training corpus)"
DELAY_S = 1.2  # polite rate limit between requests

# Boards chosen for signal density on the project's actual subject matter.
DEFAULT_BOARDS = {
    "1": "Bitcoin Discussion",
    "6": "Development & Technical Discussion",
    "7": "Economics",
    "42": "Mining",
    "67": "Legal",
    "53": "Alternate cryptocurrencies (Announcements)",
}


class TextExtractor(HTMLParser):
    """Minimal, dependency-free extraction of visible post text from SMF markup."""
    def __init__(self):
        super().__init__()
        self.in_post = False
        self.depth = 0
        self.chunks: list[str] = []
        self.skip_tags = {"script", "style"}
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        cls = attrs.get("class", "")
        if tag == "div" and "post" in cls.split():
            self.in_post = True
            self.depth = 0
        elif self.in_post:
            self.depth += 1
        if tag in self.skip_tags:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self.skip_tags and self.skip_depth > 0:
            self.skip_depth -= 1
        if self.in_post:
            if self.depth == 0:
                self.in_post = False
            else:
                self.depth -= 1

    def handle_data(self, data):
        if self.in_post and self.skip_depth == 0:
            t = data.strip()
            if t:
                self.chunks.append(t)


def fetch(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def get_thread_ids(board_id: str, n_threads: int) -> list[str]:
    """Walk a board's listing pages collecting topic IDs."""
    ids: list[str] = []
    start = 0
    pattern = re.compile(r'index\.php\?topic=(\d+)\.0')
    while len(ids) < n_threads:
        url = f"{BASE}/index.php?board={board_id}.{start}"
        try:
            html = fetch(url)
        except Exception as e:
            print(f"    board listing failed at offset {start}: {type(e).__name__}")
            break
        found = pattern.findall(html)
        if not found:
            break
        for tid in found:
            if tid not in ids:
                ids.append(tid)
        start += 40
        time.sleep(DELAY_S)
        if start > n_threads * 3:   # safety valve against infinite pagination
            break
    return ids[:n_threads]


def extract_posts(html: str) -> list[str]:
    ex = TextExtractor()
    try:
        ex.feed(html)
    except Exception:
        pass
    # SMF wraps each post's text in a div; chunks are already post-scoped by the parser.
    text = " ".join(ex.chunks)
    text = re.sub(r"\s+", " ", text).strip()
    return [text] if len(text) > 40 else []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boards", default=",".join(DEFAULT_BOARDS.keys()))
    ap.add_argument("--threads-per-board", type=int, default=200)
    ap.add_argument("--out", default=os.path.join(RAW, "bitcointalk_sample.txt"))
    a = ap.parse_args()

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    board_ids = a.boards.split(",")

    n_docs = 0
    n_chars = 0
    t0 = time.time()
    with io.open(a.out, "w", encoding="utf-8", newline="\n") as out:
        for bid in board_ids:
            bname = DEFAULT_BOARDS.get(bid, bid)
            print(f"board {bid} ({bname}): collecting thread list...", flush=True)
            tids = get_thread_ids(bid, a.threads_per_board)
            print(f"  {len(tids)} threads found")
            for i, tid in enumerate(tids, 1):
                url = f"{BASE}/index.php?topic={tid}.0"
                try:
                    html = fetch(url)
                except (urllib.error.URLError, TimeoutError) as e:
                    print(f"    [{i}/{len(tids)}] topic {tid}: fetch failed ({type(e).__name__}), skipping")
                    time.sleep(DELAY_S)
                    continue
                posts = extract_posts(html)
                for p in posts:
                    out.write(p + "\n\n")
                    n_docs += 1
                    n_chars += len(p)
                if i % 25 == 0:
                    print(f"    [{i}/{len(tids)}] {n_docs:,} posts, {n_chars/1e6:.1f}M chars, "
                          f"{time.time()-t0:.0f}s elapsed", flush=True)
                time.sleep(DELAY_S)

    digest_h = hashlib.sha256()
    with open(a.out, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest_h.update(chunk)
    digest = digest_h.hexdigest()
    size = os.path.getsize(a.out)
    est_tokens = n_chars // 4

    print(f"\nwrote {a.out}")
    print(f"  posts       : {n_docs:,}")
    print(f"  characters  : {n_chars:,}")
    print(f"  est. tokens : {est_tokens:,}")
    print(f"  elapsed     : {time.time()-t0:.0f}s")
    print(f"  sha256      : {digest}")

    with io.open(LEDGER, encoding="utf-8") as f:
        ledger = json.load(f)
    ledger["sources"] = [s for s in ledger["sources"] if s.get("slug") != "bitcointalk-sample"]
    ledger["sources"].append({
        "slug": "bitcointalk-sample",
        "name": "bitcointalk.org forum sample",
        "url": "https://bitcointalk.org",
        "license": "Individual posts retain author copyright; included as web-scraped forum "
                   "text on the same basis general web corpora (FineWeb-Edu, Common Crawl) "
                   "already include forum content. Not a separately licensed dataset.",
        "public_domain_basis": None,
        "crawl_basis": "robots.txt contains no Disallow directives (verified 2026-09-16); "
                       "crawled politely with a fixed per-request delay and an identifying "
                       "User-Agent, bounded to a fixed thread sample rather than an "
                       "unbounded crawl.",
        "published_before_generative_ai": None,   # forum is ongoing; per-post dates not extracted here
        "boards_sampled": {bid: DEFAULT_BOARDS.get(bid, bid) for bid in board_ids},
        "retrieved": date.today().isoformat(),
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "documents": n_docs,
        "characters": n_chars,
        "bytes": size,
        "estimated_tokens": est_tokens,
        "cleaning": "HTML post divs extracted, whitespace collapsed",
        "sha256_processed": digest,
        "file": os.path.relpath(a.out, ROOT).replace("\\", "/"),
        "slice": "contemporary voice (anneal + SFT only, never the pretraining spine, per D-10)",
    })
    with io.open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"\nledger updated ({len(ledger['sources'])} sources)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

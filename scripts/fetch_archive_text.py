"""Download the OCR text (`*_djvu.txt`) of archive.org items into data/raw/<dir>/.

Only for items whose rights are nameable (US Government works, Public Domain Mark, CC BY);
the licence check happens BEFORE this script runs and is recorded by ledger_add_text.py.

    python scripts/fetch_archive_text.py usgov NEETSModule01=neets-01-dc.txt mutcd2009edition_202401=fhwa-mutcd-2009.txt
"""

from __future__ import annotations

import io
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "pagouro-corpus-builder/1.0 (+https://github.com/ericrwade/pagouro)"}


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    outdir = os.path.join(ROOT, "data", "raw", sys.argv[1])
    os.makedirs(outdir, exist_ok=True)
    for spec in sys.argv[2:]:
        ident, _, fname = spec.partition("=")
        fname = fname or f"{ident}.txt"
        meta = json.load(urllib.request.urlopen(urllib.request.Request(f"https://archive.org/metadata/{ident}", headers=UA)))
        txts = [f for f in meta.get("files", []) if f["name"].endswith("_djvu.txt")]
        if not txts:
            print(f"{ident}: no _djvu.txt (formats: {sorted({f.get('format') for f in meta.get('files', [])})[:8]})")
            continue
        m = meta.get("metadata", {})
        url = f"https://archive.org/download/{ident}/{urllib.parse.quote(txts[0]['name'])}"
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read().decode("utf-8", errors="replace")
        path = os.path.join(outdir, fname)
        io.open(path, "w", encoding="utf-8", newline="\n").write(data)
        print(f"{ident}: {len(data):,} chars -> {os.path.relpath(path, ROOT)} | title={str(m.get('title'))[:60]!r} "
              f"date={m.get('date')} licenseurl={m.get('licenseurl')} rights={str(m.get('rights'))[:60]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

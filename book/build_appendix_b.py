"""Generate Appendix B — the ledger, printed — from corpus.json.

    python book/build_appendix_b.py      -> book/chapters/B-ledger.md

One row per source: what it is, the licence or public-domain basis, how many tokens, its date
basis, and where it sits (backbone / canon / shelf / synthetic / pack / superseded / excluded).
Regenerated, never hand-edited.
"""

from __future__ import annotations

import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "corpus.json")
OUT = os.path.join(ROOT, "book", "chapters", "B-ledger.md")


def where(s: dict) -> str:
    sl = str(s.get("slice", "") or "")
    if sl.startswith("SUPERSEDED"):
        return "superseded"
    if sl.startswith("EXCLUDED"):
        return "excluded"
    if sl.startswith("shelf"):
        return "shelf (anneal)"
    if sl.startswith("pack"):
        return "pack only"
    if "synthetic" in sl.lower() or "synthetic" in s["slug"]:
        return "synthetic (SFT)"
    if sl == "domain canon":
        return "canon (anneal)"
    return "backbone"


def date_basis(s: dict) -> str:
    db = s.get("date_basis")
    if isinstance(db, dict):
        if "dump_date" in db:
            return f"dump {db['dump_date']}"
        if "histogram" in db:
            keys = sorted(db["histogram"])
            return f"crawl dumps {keys[0][-7:]}…{keys[-1][-7:]}"
        return "dated"
    if isinstance(db, str) and db.startswith("CAVEAT"):
        return "caveat: collected ≤ 2022-03-31"
    if s.get("date_filter"):
        return "per-row < 2022-01-01"
    if s.get("first_published"):
        return f"published {s['first_published']}"
    if s.get("published_before_generative_ai") is True:
        return "pre-2022"
    return "—"


def cell(x) -> str:
    return str(x).replace("|", "/").replace("\n", " ")


def main() -> int:
    d = json.load(io.open(SRC, encoding="utf-8"))
    rows = d["sources"]
    order = {"backbone": 0, "canon (anneal)": 1, "shelf (anneal)": 2, "synthetic (SFT)": 3, "pack only": 4, "superseded": 5, "excluded": 6}
    rows = sorted(rows, key=lambda s: (order[where(s)], -(s.get("estimated_tokens") or 0)))
    active = [s for s in rows if where(s) not in ("superseded", "excluded", "pack only")]
    tot = sum(s.get("estimated_tokens") or 0 for s in active)
    out = ["# Appendix B — The ledger, printed",
           "",
           f"*Generated from `corpus.json` by `book/build_appendix_b.py`: {len(rows)} rows, of which {len(active)} are in a "
           f"training mixture ({tot/1e6:,.0f}M estimated tokens). Superseded and excluded rows stay in the file — a ledger "
           "that deletes its mistakes is a marketing document. Every row in the file also carries the SHA-256 of the "
           "processed text, the retrieval timestamp, and the cleaning applied; `scripts/verify_ledger.py` checks the "
           "hashes against the files.*",
           "", "| Where | Source | Licence / basis | Tokens | Date basis |", "|---|---|---|---|---|"]
    for s in rows:
        lic = s.get("license", "")
        if len(lic) > 70:
            lic = lic[:67] + "…"
        toks = s.get("estimated_tokens")
        out.append(f"| {where(s)} | {cell(s.get('name') or s['slug'])[:80]} | {cell(lic)} | "
                   f"{'' if toks is None else f'{toks/1e6:,.1f}M'} | {cell(date_basis(s))} |")
    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print(f"wrote {OUT}: {len(rows)} rows, {len(active)} active, {tot/1e6:,.0f}M tokens")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

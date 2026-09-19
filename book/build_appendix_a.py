"""Generate Appendix A — every decision in one table — from docs/DECISIONS.md.

    python book/build_appendix_a.py      -> book/chapters/A-decisions.md

Parses each `### D-NN — title` / `### O-NN — title` heading and the first bold date/author lead
of its body. Regenerated, never hand-edited: the decisions file stays the source of truth.
"""

from __future__ import annotations

import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "DECISIONS.md")
OUT = os.path.join(ROOT, "book", "chapters", "A-decisions.md")

HEAD = re.compile(r"^### (D|O)-(\d+)(?:\s*/\s*O-\d+)?(?:\s+proposal)?\s+[—-]+\s+(.+?)\s*$", re.M)
OPEN_ROW = re.compile(r"^\| (O-\d+) \| ([^|]+) \|", re.M)
CLOSES = re.compile(r"[Cc]loses (O-\d+)")
LEAD = re.compile(r"\*\*(20\d\d-\d\d-\d\d)[^*]*\*\*")


def main() -> int:
    text = io.open(SRC, encoding="utf-8").read()
    heads = list(HEAD.finditer(text))
    rows = []
    for i, m in enumerate(heads):
        body = text[m.end(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        kind, num, title = m.group(1), int(m.group(2)), m.group(3)
        title = re.sub(r"\s+", " ", title).replace("|", "\\|")
        d = LEAD.search(body)
        date = d.group(1) if d else ""
        locked = "LOCKED" in title.upper() or "**LOCKED" in body[:200].upper()
        rows.append((kind, num, date, title, locked))
    decisions = sorted([r for r in rows if r[0] == "D"], key=lambda r: r[1])
    # Open items: the OPEN table at the top plus any "### O-NN" proposals below; an item is closed
    # when a decision says "Closes O-NN".
    closed = {}
    for i, m in enumerate(heads):
        if m.group(1) != "D":
            continue
        body = text[m.end(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        for c in CLOSES.findall(body + m.group(0)):
            closed[c] = f"D-{m.group(2)}"
    table = {m.group(1): re.sub(r"\s+", " ", m.group(2)).strip() for m in OPEN_ROW.finditer(text)}
    for kind, num, date, title, locked in rows:
        if kind == "O":
            table.setdefault(f"O-{num}", title)
    opens = sorted(table.items(), key=lambda kv: int(kv[0][2:]))
    out = ["# Appendix A — Every decision, in one table",
           "",
           f"*Generated from `docs/DECISIONS.md` by `book/build_appendix_a.py`; {len(decisions)} decisions, "
           f"{len(opens)} open items with their own heading or table row (items raised inline — O-14, O-19, "
           f"O-20, O-22, O-25 — live in the decisions that raised them). The file itself carries the reasoning; this is the map.*",
           "", "## Decisions", "", "| # | Date | Decision |", "|---|---|---|"]
    for kind, num, date, title, locked in decisions:
        out.append(f"| D-{num} | {date} | {title}{' **(locked)**' if locked else ''} |")
    out += ["", "## Open items (Eric's calls, or waiting on a measurement)", "", "| # | Item | Status |", "|---|---|---|"]
    for oid, title in opens:
        out.append(f"| {oid} | {title.replace('|', '/')} | {'closed by ' + closed[oid] if oid in closed else 'open'} |")
    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print(f"wrote {OUT}: {len(decisions)} decisions, {len(opens)} open items")
    missing = [f"{k}-{n}" for k, n, d, t, l in rows if not d]
    if missing:
        print("no date lead found for:", ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

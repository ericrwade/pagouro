"""Assemble the book: regenerate the generated appendices, then concatenate every chapter in
outline order into book/MAKE_YOUR_OWN_AI.md (one Markdown file; pandoc can make EPUB/PDF).

    python book/build.py
"""

from __future__ import annotations

import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "book")
CH = os.path.join(BOOK, "chapters")
OUT = os.path.join(BOOK, "MAKE_YOUR_OWN_AI.md")


def key(fn: str):
    m = re.match(r"^(\d+)|^([A-Z])", fn)
    if m and m.group(1):
        return (0, int(m.group(1)), fn)
    return (1, m.group(2) if m else "Z", fn)


def main() -> int:
    for gen in ("build_appendix_a.py", "build_appendix_b.py"):
        subprocess.run([sys.executable, os.path.join(BOOK, gen)], check=True)
    files = sorted((f for f in os.listdir(CH) if f.endswith(".md")), key=key)
    parts = ["# Make Your Own AI\n\n*The story of Pagouro, with the instructions in the same pages. Working draft; "
             "chapters present are listed below, the rest are in `book/OUTLINE.md`.*\n"]
    words = 0
    for f in files:
        text = io.open(os.path.join(CH, f), encoding="utf-8").read().strip() + "\n"
        words += len(text.split())
        parts.append("\n\n---\n\n" + text)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write("".join(parts))
    story = [f for f in files if f[:2].isdigit() and "do-it" not in f]
    print(f"wrote {OUT}: {len(files)} chapters, {words:,} words "
          f"({len(story)} story/all-rights-reserved, {len(files) - len(story)} CC BY-SA 4.0; D-64)")
    for f in files:
        print("  ", f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

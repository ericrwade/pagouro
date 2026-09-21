"""House style applied to what the model says (D-78). Standard library only. Conventions, not facts:
the model's answer is rewritten only where a *notation* is house style, never where a claim is.

  * Eras are BC and AD, never BCE / CE.  "500 CE" -> "AD 500"; "c. 300 BCE" -> "c. 300 BC";
    "the 3rd century CE" -> "the 3rd century AD".
  * Celestial events are dated as observed on Earth. The rewrite cannot know astronomy, so this one
    is a *seed* rule (sft/style_seed.jsonl) plus a light touch here: "SN 1987A exploded in 1987" is
    left alone (the model learned the phrasing from the seed, or it did not), but the guide says why.

The rules live in docs/STYLE_GUIDE.md, which ships beside the executable.
"""

from __future__ import annotations

import re

_BCE = re.compile(r"\b(\d{1,4}(?:,\d{3})?)\s*BCE\b")
_CE_AFTER = re.compile(r"\b(\d{1,4}(?:,\d{3})?)\s*CE\b")
_CENTURY_CE = re.compile(r"\b(\d{1,2}(?:st|nd|rd|th)\s+(?:century|millennium))\s+CE\b", re.I)
_CENTURY_BCE = re.compile(r"\b(\d{1,2}(?:st|nd|rd|th)\s+(?:century|millennium))\s+BCE\b", re.I)
_BARE_BCE = re.compile(r"\bBCE\b")
_BARE_CE = re.compile(r"(?<=\d )CE\b|\bC\.E\.")


def eras(text: str) -> str:
    text = _CENTURY_BCE.sub(r"\1 BC", text)
    text = _CENTURY_CE.sub(r"\1 AD", text)
    text = _BCE.sub(r"\1 BC", text)
    text = _CE_AFTER.sub(r"AD \1", text)
    text = _BARE_BCE.sub("BC", text)
    return text


def apply(text: str) -> str:
    return eras(text)


if __name__ == "__main__":
    for s in ["Rome was founded in 753 BCE and the empire fell in 476 CE.", "In the 3rd century CE, and c. 300 BCE.",
              "The year 1,200 CE.", "BCE dates are common."]:
        print(s, "->", apply(s))

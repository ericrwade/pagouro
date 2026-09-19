"""Fetch Bitcoin BIPs and Ethereum EIPs as shelf text (D-58), from each repo's LAST COMMIT BEFORE
1 JANUARY 2022 (D-34: nothing collected or published after the generative-AI cutoff), keeping only
documents whose own header names an acceptable licence.

- BIPs (github.com/bitcoin/bips): BIP-2 requires a `License:` header. Kept licences: BSD-2-Clause,
  BSD-3-Clause, CC0-1.0, MIT, CC-BY-4.0, CC-BY-SA-4.0, PD, GNU-All-Permissive, OPL; "A OR B" counts
  if either side is acceptable. Documents with no header or another licence are dropped and counted.
- EIPs (github.com/ethereum/EIPs; in 2021 this still held the ERCs): no repo-level LICENSE file at
  the snapshot; EIP-1 requires every document to carry the CC0 waiver sentence, and only documents
  that do are kept (withdrawn/moved ones dropped).

Output: data/raw/specs/{bips,eips}.txt (one document per block with number, title, authors,
licence) plus ATTRIBUTION-bips.txt for the attribution licences. Prints the snapshot commits.

    python scripts/fetch_bips_eips.py
"""

from __future__ import annotations

import collections
import io
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "raw", "specs")
CUTOFF = "2022-01-01"
BIP_OK = {"BSD-2-Clause", "BSD-3-Clause", "CC0-1.0", "MIT", "CC-BY-4.0", "CC-BY-SA-4.0", "PD",
          "GNU-All-Permissive", "OPL"}
CC0_RE = re.compile(r"Copyright and related rights waived via\s+\[?CC0", re.I)


def git(*args: str, cwd: str | None = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def clone_before_cutoff(url: str, dst: str, only: str) -> tuple[str, str]:
    """Clone history since a month before CUTOFF (full blobs for those commits -- a blobless
    clone's lazy fetch left 69/153 BIP files unreadable), sparse-checkout `only` (the EIPs repo has
    asset filenames Windows cannot create), then check out the last commit before CUTOFF.
    Returns (hash, committer date)."""
    git("clone", "--quiet", "--shallow-since=2021-11-01", "--no-checkout", url, dst)
    if only != ".":
        git("sparse-checkout", "set", "--no-cone", f"/{only}/", cwd=dst)
    commit = git("rev-list", "-1", f"--before={CUTOFF}T00:00:00Z", "HEAD", cwd=dst)
    date = git("show", "-s", "--format=%cI", commit, cwd=dst)
    git("checkout", "--quiet", commit, cwd=dst)
    missing = git("status", "--short", cwd=dst)
    if missing:
        raise SystemExit(f"{url}: checkout incomplete ({len(missing.splitlines())} paths) -- stop and look")
    return commit, date


def header_field(text: str, name: str) -> str:
    m = re.search(rf"^\s*{name}:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def bip_license(text: str) -> list[str]:
    m = re.search(r"^\s*License:\s*(.+?)(?=^\s*[A-Z][A-Za-z-]+:|^</pre>|^\S)", text, re.M | re.S)
    if not m:
        return []
    return [t.strip() for t in re.split(r"[\n,]|\bOR\b", m.group(1)) if t.strip()]


def do_bips(tmp: str) -> dict:
    d = os.path.join(tmp, "bips")
    commit, date = clone_before_cutoff("https://github.com/bitcoin/bips.git", d, ".")
    kept, dropped, hist, attrib = [], collections.Counter(), collections.Counter(), []
    for fn in sorted(os.listdir(d)):
        if not re.match(r"bip-\d{4}\.(mediawiki|md)$", fn):
            continue
        text = io.open(os.path.join(d, fn), encoding="utf-8", errors="replace").read()
        lic = bip_license(text)
        if not lic:
            dropped["no-license-header"] += 1
            continue
        if not any(l in BIP_OK for l in lic):
            dropped["|".join(lic)] += 1
            continue
        hist["|".join(sorted(lic))] += 1
        title, authors = header_field(text, "Title"), header_field(text, "Author")
        kept.append(f"=== {fn.split('.')[0].upper()}: {title}\nAuthors: {authors}\nLicense: {', '.join(lic)}\n\n{text.strip()}\n")
        if any(l.startswith(("CC-BY", "BSD", "MIT")) for l in lic):
            attrib.append(f"{fn}: {title} — {authors} — {', '.join(lic)}")
    io.open(os.path.join(OUT, "bips.txt"), "w", encoding="utf-8", newline="\n").write("\n\n".join(kept))
    io.open(os.path.join(OUT, "ATTRIBUTION-bips.txt"), "w", encoding="utf-8", newline="\n").write(
        f"Documents from github.com/bitcoin/bips at commit {commit} ({date}) used under their stated "
        "licences; attribution licences listed:\n\n" + "\n".join(attrib) + "\n")
    return {"commit": commit, "commit_date": date, "kept": len(kept), "dropped": dict(dropped), "licences": dict(hist)}


def do_eips(tmp: str) -> dict:
    d = os.path.join(tmp, "eips")
    commit, date = clone_before_cutoff("https://github.com/ethereum/EIPs.git", d, "EIPS")
    # The 2021 snapshot has no repo-level LICENSE file; EIP-1 requires each document to carry the
    # CC0 waiver sentence, and that sentence is the licence line we rely on -- no sentence, no use.
    sub = os.path.join(d, "EIPS")
    kept, dropped = [], collections.Counter()
    for fn in sorted(os.listdir(sub)):
        if not fn.endswith(".md"):
            continue
        text = io.open(os.path.join(sub, fn), encoding="utf-8", errors="replace").read()
        if not CC0_RE.search(text):
            dropped["no-cc0-waiver"] += 1
            continue
        status = header_field(text, "status")
        if status.lower() in {"withdrawn", "moved"}:
            dropped[f"status-{status.lower()}"] += 1
            continue
        title, authors = header_field(text, "title"), header_field(text, "author")
        kept.append(f"=== {fn[:-3].upper()}: {title}\nAuthors: {authors}\nStatus: {status}\nLicense: CC0-1.0\n\n{text.strip()}\n")
    io.open(os.path.join(OUT, "eips.txt"), "w", encoding="utf-8", newline="\n").write("\n\n".join(kept))
    return {"commit": commit, "commit_date": date, "kept": len(kept), "dropped": dict(dropped),
            "license": "CC0-1.0 per-document waiver (EIP-1)"}


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="specs_")
    print("BIPs:", do_bips(tmp))
    print("EIPs:", do_eips(tmp))
    for fn in ("bips.txt", "eips.txt"):
        print(fn, f"{os.path.getsize(os.path.join(OUT, fn)):,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())

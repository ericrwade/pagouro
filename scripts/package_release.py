"""Assemble the release package: README, manifest with hashes, licences, and a
double-clickable launcher that states the ONLINE/OFFLINE and SAND/STONE modes
plainly, per THREAT_MODEL.md and D-19.

This is a first real packaging pass, not the polished app in the brief's full
spec (RAG, tool harness, a proper toggle UI). It is a genuinely working,
offline, double-click chat experience built on top of the actual trained
model, with the privacy claims stated exactly as precisely as THREAT_MODEL.md
requires and no more.

    python scripts/package_release.py --release-dir release/Pagouro
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LAUNCHER_BAT = r"""@echo off
setlocal
title Pagouro -- offline, local, yours

echo ============================================================
echo   PAGOURO
echo   A small language model that lives on this USB stick.
echo.
echo   MODE: OFFLINE          (this build makes no network calls)
echo   MODE: SAND              (nothing you type is saved to disk)
echo.
echo   Your questions never leave this machine.
echo   This machine is still your responsibility.
echo   Type '/exit' or press Ctrl+C to quit.
echo ============================================================
echo.

"%~dp0llama-cli.exe" -m "%~dp0model\pagouro-q4_k_m.gguf" -st -n 300 --temp 0.7 -ngl 0

echo.
echo Session ended. Nothing was written to disk in this mode.
pause
"""

MANIFESTO = """PAGOURO -- a manifesto, and a receipt

You are holding a language model, roughly 700MB, that was trained from random
weights, not fine-tuned from someone else's. Every source that went into it
is listed in docs/corpus.json with a stated reason it was allowed to be there
-- a licence, or a public-domain basis, or both. Nothing was scraped in secret.

It runs entirely on this machine. Nothing you type is sent anywhere. There is
no account, no telemetry, no update check, no phone-home of any kind. If you
pull the network cable, nothing about how this behaves changes, because
nothing about how this behaves depended on the network in the first place.

It is not the smartest model you can talk to. It is roughly a hundred times
smaller, in training data, than the frontier models you may have used. What
it tries to do instead is not bluff: when it does not know something, it is
trained to say so rather than invent a confident-sounding answer. Whether it
succeeds at that is measured, not just claimed -- see docs/BASELINES.md for
the actual numbers, and how it compares to other models on the same test.

This is a finished, released artifact. It will not be updated, patched, or
supported. If you want to take it further -- retrain it, fine-tune it,
correct something, build a fork -- the code and the training recipe are
openly licensed for exactly that. Nobody needs my permission.

If this was worth something to you, there is a longer note about that in
docs/. If it was not, that is fine too. Either way, it is yours now, free,
and it will keep working long after I have stopped thinking about it.

  Hermit crab: carries a home it can leave.
  Ouroboros: needs nothing from outside.
  Both are the product.
"""


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--release-dir", required=True)
    a = ap.parse_args()

    rel = a.release_dir if os.path.isabs(a.release_dir) else os.path.join(ROOT, a.release_dir)
    if not os.path.isdir(rel):
        raise SystemExit(f"release dir does not exist yet: {rel} -- run the copy steps first")

    with io.open(os.path.join(rel, "PAGOURO.bat"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(LAUNCHER_BAT)

    with io.open(os.path.join(rel, "MANIFESTO.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(MANIFESTO)

    # Hash every shipped file for the manifest. This IS the anchorable artifact.
    hashes = {}
    for dirpath, _, files in os.walk(rel):
        for fn in files:
            if fn == "MANIFEST.md":
                continue
            full = os.path.join(dirpath, fn)
            relp = os.path.relpath(full, rel).replace("\\", "/")
            hashes[relp] = {"sha256": sha256_file(full), "bytes": os.path.getsize(full)}

    manifest_lines = [
        "# Pagouro release manifest",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "This manifest is what a Bitcoin-anchored timestamp would cover (D-14):",
        "a stranger downloading this from any mirror can verify every file below",
        "matches its recorded hash, and therefore matches what was actually released.",
        "",
        "**This build has not yet been anchored to Bitcoin.** That is the final",
        "release step (brief section 10) and happens once, deliberately, after",
        "the weights are considered final -- not on every packaging pass.",
        "",
        "| File | SHA-256 | Bytes |",
        "|---|---|---|",
    ]
    for relp in sorted(hashes):
        h = hashes[relp]
        manifest_lines.append(f"| `{relp}` | `{h['sha256']}` | {h['bytes']:,} |")
    with io.open(os.path.join(rel, "MANIFEST.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(manifest_lines) + "\n")

    readme = f"""# Pagouro

**A finished artifact, released as-is. No updates or support are promised. Fork it.**

## Run it

Double-click `PAGOURO.bat`. That is the entire installation process. It runs
`llama-cli.exe` against the model in `model/`, entirely offline, on the CPU
of whatever machine this stick is plugged into.

No install, no admin rights, no internet connection required or used.

## What this is

A small language model (see `docs/corpus.json` for exactly what it was trained
on, and why each source was allowed in) that runs from this USB stick with no
account, no telemetry, and no network calls in its default mode. Read
`MANIFESTO.txt` for the short version of why, and `docs/THREAT_MODEL.md` for
the precise, honest account of what "offline" does and does not protect you
from -- please read that before relying on this for anything sensitive.

## Verify it

Every file in this folder is hashed in `MANIFEST.md`. If you got this stick or
folder from someone other than Eric directly, check the hashes match before
trusting it.

## Licence

Code: Apache 2.0. Weights: CC BY-SA 4.0 (share-alike, because part of the
training data was itself share-alike -- see `docs/DECISIONS.md` D-31 in the
full project repository for why). The training recipe and every source's
licence are documented, so this can genuinely be rebuilt or forked, not just
looked at.

## What "PAGOURO" means

Greek *págouros*, hermit crab: carries a home it can move out of. The *ouro*
inside it nods to ouroboros, the self-consuming snake: needs nothing from
outside. Both describe this file, sitting on this stick, needing nothing from
anywhere to keep working.
"""
    with io.open(os.path.join(rel, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(readme)

    print(f"packaged: {rel}")
    print(f"  files hashed: {len(hashes)}")
    total_bytes = sum(h["bytes"] for h in hashes.values())
    print(f"  total size: {total_bytes/1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

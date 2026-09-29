"""Check every file on this stick against MANIFEST.md. Standard library only; no network.

    python verify_manifest.py            # run from the release folder (or pass the folder)
    python verify_manifest.py D:\\Pagouro

Prints one line per mismatch, then a verdict. Exit code 0 = every listed file matches and no
listed file is missing; 1 otherwise. Extra files not in the manifest are reported but do not
fail the check (you may have saved notes or transcripts in workspace/).

If MANIFEST.md.minisig is present and `minisign` is installed, the signature is checked too
(the public key is printed in the README and the manifesto; compare it by eye).
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import shutil
import subprocess
import sys

ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|\s*([\d,]+)\s*\|")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__)))
    manifest = os.path.join(root, "MANIFEST.md")
    if not os.path.exists(manifest):
        print(f"no MANIFEST.md in {root}")
        return 1
    listed = {}
    for line in io.open(manifest, encoding="utf-8"):
        m = ROW.match(line)
        if m:
            listed[m.group(1)] = (m.group(2), int(m.group(3).replace(",", "")))
    bad = missing = 0
    seen = set()
    for relp, (digest, size) in sorted(listed.items()):
        full = os.path.join(root, *relp.split("/"))
        if not os.path.exists(full):
            print(f"MISSING   {relp}")
            missing += 1
            continue
        seen.add(relp)
        actual_size = os.path.getsize(full)
        actual = sha256_file(full)
        if actual != digest or actual_size != size:
            print(f"MISMATCH  {relp}  (manifest {digest[:12]}.. {size:,} B; found {actual[:12]}.. {actual_size:,} B)")
            bad += 1
    extra = []
    skip = {"MANIFEST.md", "MANIFEST.md.minisig", "MANIFEST.md.ots"}
    for dirpath, _, files in os.walk(root):
        for fn in files:
            relp = os.path.relpath(os.path.join(dirpath, fn), root).replace("\\", "/")
            if relp not in listed and relp not in skip and not relp.startswith("workspace/"):
                extra.append(relp)
    for relp in sorted(extra):
        print(f"EXTRA     {relp}  (not in the manifest)")

    sig = manifest + ".minisig"
    if os.path.exists(sig):
        exe = shutil.which("minisign")
        if exe:
            pub = next((os.path.join(root, n) for n in ("pagouro.pub", "minisign.pub")
                        if os.path.exists(os.path.join(root, n))), os.path.join(root, "minisign.pub"))
            cmd = [exe, "-V", "-m", manifest, "-x", sig] + (["-p", pub] if os.path.exists(pub) else [])
            r = subprocess.run(cmd, capture_output=True, text=True)
            print(("SIGNATURE OK: " if r.returncode == 0 else "SIGNATURE FAILED: ") + (r.stdout + r.stderr).strip())
            if r.returncode != 0:
                bad += 1
        else:
            print("signature file present but `minisign` is not installed; hashes checked only")

    ok = bad == 0 and missing == 0
    print(f"\n{len(seen)} of {len(listed)} listed files present, {bad} mismatched, {missing} missing, {len(extra)} extra")
    print("VERDICT: every listed file matches the manifest" if ok else "VERDICT: this stick does NOT match its manifest")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

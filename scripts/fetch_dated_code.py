"""Dated, licence-checked code to replace The Stack (D-62b, D-34): every repository below is
cloned with history since a month before the cutoff and checked out at its LAST COMMIT BEFORE
1 JANUARY 2022; its LICENSE file is read and classified — only MIT / BSD / Apache-2.0 / ISC /
PSF / HPND / CC0 repos are kept, MPL excluded (any GPL/LGPL/AGPL/BUSL/SSPL/MPL: skipped,
counted). Source files of the target language are concatenated (vendored, generated, minified,
test-fixture and binary-ish paths dropped) into data/raw/code/<lang>.txt, and a ledger row per
repository (url, commit, commit date, licence as classified, file count, chars, tokens, sha256)
is appended to corpus.json via scripts/ledger_add_text.py-compatible JSON in data/raw/code/rows.json.

    python scripts/fetch_dated_code.py --lang python            # one language
    python scripts/fetch_dated_code.py                          # all five (re-runs retry skipped repos, keep done ones)

The list is curated by hand: well-known, permissively licensed, active before 2022. No
copyleft repos even where they are famous (go-ethereum LGPL, Uniswap v2 GPL, Aave AGPL...).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "raw", "code")
CUTOFF = "2022-01-01"

REPOS = {
    "python": [
        "https://github.com/python/cpython", "https://github.com/django/django", "https://github.com/pallets/flask",
        "https://github.com/psf/requests", "https://github.com/numpy/numpy", "https://github.com/pandas-dev/pandas",
        "https://github.com/scikit-learn/scikit-learn", "https://github.com/scrapy/scrapy", "https://github.com/tiangolo/fastapi",
        "https://github.com/sqlalchemy/sqlalchemy", "https://github.com/pypa/pip", "https://github.com/sympy/sympy",
        "https://github.com/boto/boto3", "https://github.com/tornadoweb/tornado", "https://github.com/celery/celery",
        "https://github.com/home-assistant/core", "https://github.com/pallets/jinja", "https://github.com/pallets/click",
        "https://github.com/encode/httpx", "https://github.com/encode/starlette", "https://github.com/samuelcolvin/pydantic",
        "https://github.com/python-pillow/Pillow", "https://github.com/pytest-dev/pytest", "https://github.com/psf/black",
        "https://github.com/matplotlib/matplotlib", "https://github.com/bitcoin-core/HWI", "https://github.com/petertodd/python-bitcoinlib",
        "https://github.com/ethereum/web3.py", "https://github.com/ethereum/py-evm",
    ],
    "rust": [
        "https://github.com/rust-lang/rust", "https://github.com/tokio-rs/tokio", "https://github.com/serde-rs/serde",
        "https://github.com/rust-lang/cargo", "https://github.com/BurntSushi/ripgrep", "https://github.com/actix/actix-web",
        "https://github.com/diesel-rs/diesel", "https://github.com/rust-analyzer/rust-analyzer", "https://github.com/bytecodealliance/wasmtime",
        "https://github.com/bevyengine/bevy", "https://github.com/tikv/tikv", "https://github.com/solana-labs/solana",
        "https://github.com/rustls/rustls", "https://github.com/hyperium/hyper", "https://github.com/clap-rs/clap",
        "https://github.com/rust-bitcoin/rust-bitcoin", "https://github.com/paritytech/substrate", "https://github.com/sharkdp/bat",
        "https://github.com/alacritty/alacritty", "https://github.com/rust-lang/rustlings",
    ],
    "go": [
        "https://github.com/golang/go", "https://github.com/kubernetes/kubernetes", "https://github.com/moby/moby",
        "https://github.com/etcd-io/etcd", "https://github.com/prometheus/prometheus", "https://github.com/gohugoio/hugo",
        "https://github.com/gin-gonic/gin", "https://github.com/spf13/cobra", "https://github.com/grpc/grpc-go",
        "https://github.com/cosmos/cosmos-sdk", "https://github.com/ipfs/go-ipfs", "https://github.com/caddyserver/caddy",
        "https://github.com/traefik/traefik", "https://github.com/btcsuite/btcd", "https://github.com/lightningnetwork/lnd",
        "https://github.com/tendermint/tendermint", "https://github.com/hashicorp/consul", "https://github.com/junegunn/fzf",
    ],
    "solidity": [
        "https://github.com/OpenZeppelin/openzeppelin-contracts", "https://github.com/compound-finance/compound-protocol",
        "https://github.com/ensdomains/ens-contracts", "https://github.com/smartcontractkit/chainlink",
        "https://github.com/0xProject/protocol",   # Synthetixio/synthetix: repository gone; sushiswap/sushiswap: history rewritten, nothing before 2022
        "https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable",   # Loopring/protocols: repository gone
        "https://github.com/ethereum-optimism/optimism", "https://github.com/rarible/protocol-contracts", "https://github.com/1inch/limit-order-protocol",
        "https://github.com/decentraland/marketplace-contracts",
        # tried and out (first run, 2026-09-21): ethereum/solidity GPL-3, balancer-core GPL-3, ds-token GPL-3, yearn-vaults AGPL, argent GPL-3, conditional-tokens LGPL
    ],
    "cpp": [   # the 1B plan's code slice names C++ (docs/JOB_1B.md); the Stack rows never covered it
        "https://github.com/bitcoin/bitcoin", "https://github.com/monero-project/monero", "https://github.com/jedisct1/libsodium",
        "https://github.com/abseil/abseil-cpp", "https://github.com/protocolbuffers/protobuf", "https://github.com/grpc/grpc",
        "https://github.com/facebook/folly", "https://github.com/fmtlib/fmt", "https://github.com/nlohmann/json",
        "https://github.com/google/googletest", "https://github.com/google/leveldb", "https://github.com/facebook/zstd",
        "https://github.com/simdjson/simdjson", "https://github.com/skypjack/entt", "https://github.com/ocornut/imgui",
        "https://github.com/godotengine/godot", "https://github.com/opencv/opencv", "https://github.com/google/re2",
        "https://github.com/microsoft/terminal", "https://github.com/electron/electron", "https://github.com/apple/foundationdb",
        "https://github.com/ethereum/aleth",                      # ethereum/solidity itself is GPL-3: out
    ],
}
EXT = {"python": (".py",), "rust": (".rs",), "go": (".go",), "solidity": (".sol",), "cpp": (".cc", ".cpp", ".cxx", ".h", ".hpp", ".hh")}
SKIP_DIRS = re.compile(r"(^|/)(vendor|third_party|thirdparty|node_modules|\.git|testdata|fixtures|_vendor|Godeps|build|dist|target|\.eggs|__pycache__)(/|$)", re.I)
SKIP_FILES = re.compile(r"(\.min\.|\.pb\.go$|_generated\.|\.generated\.|zz_generated|\.gen\.|autogen|/migrations/\d)", re.I)
ALLOWED = {
    "MIT": r"Permission is hereby granted, free of charge",
    "BSD": r"Redistribution and use in source and binary forms",
    "Apache-2.0": r"Apache License,?\s*Version 2\.0",
    "ISC": r"ISC License|Permission to use, copy, modify, and/or distribute this software for any purpose",
    "PSF": r"PYTHON SOFTWARE FOUNDATION LICENSE",
    "Unlicense": r"This is free and unencumbered software released into the public domain",
    "0BSD": r"Zero-Clause BSD|0BSD",
    "CC0-1.0": r"CC0 1\.0 Universal",       # a public-domain dedication (rust-bitcoin)
    "HPND": r"Permission to use, copy, modify,? and distribute this\s+software and its\s+(associated\s+)?documentation\s+for any purpose and without fee is hereby granted",   # licence texts wrap at 72 cols   # Pillow
    "matplotlib (PSF-style)": r"License agreement for matplotlib",   # PSF-derived, BSD-compatible
}
FORBIDDEN = re.compile(r"GNU (GENERAL|LESSER|AFFERO) PUBLIC LICENSE|Business Source License|Server Side Public License|Mozilla Public License|Commons Clause", re.I)


def git(*args: str, cwd: str | None = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()


def classify_license(repo_dir: str):
    """(licence, file, note). Reads every licence-named file in the repo root; the first one that
    names a permitted licence before any copyleft mention wins (bevy's LICENSE is a pointer to
    LICENSE-MIT / LICENSE-APACHE; cpython's PSF text cites the GPL in a choice-of-law clause)."""
    forbidden_note = ""
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENSE-MIT", "LICENSE-APACHE", "LICENSE-Apache", "LICENSE.MIT", "LICENSE.BSD", "LICENSE.Apache", "COPYING", "LICENSE.rst", "license", "LICENCE"):
        p = os.path.join(repo_dir, name)
        if os.path.isdir(p):                         # matplotlib keeps a LICENSE/ folder: its own text is LICENSE/LICENSE
            p = os.path.join(p, "LICENSE")
        if not os.path.isfile(p):
            continue
        text = io.open(p, encoding="utf-8", errors="replace").read()
        first_ok = min(((m.start(), lic) for lic, pat in ALLOWED.items() for m in [re.search(pat, text, re.I)] if m), default=None)
        bad = FORBIDDEN.search(text)
        if first_ok and (not bad or first_ok[0] < bad.start()):
            return first_ok[1], name, text[:120].replace("\n", " ")
        if bad:
            forbidden_note = forbidden_note or f"copyleft/source-available in {name}: {bad.group(0)}"
    return None, "", forbidden_note or "no licence file with a recognised permissive text"


def _rmtree(path: str) -> None:
    """rmtree that survives git's read-only pack files on Windows."""
    def _onerror(fn, p, exc):
        try:
            os.chmod(p, 0o700); fn(p)
        except OSError:
            pass
    shutil.rmtree(path, onerror=_onerror)


def fetch_repo(url: str, lang: str, tmp: str):
    name = url.rstrip("/").rsplit("/", 1)[-1]
    dst = os.path.join(tmp, name)
    t0 = time.time()
    try:
        git("clone", "--quiet", "--shallow-since=2021-11-15", "--no-checkout", "--single-branch", url, dst)
    except subprocess.CalledProcessError as e:
        try:   # a failed shallow clone (an odd default branch, a partial transfer): full history, lazy blobs
            _rmtree(dst)
            git("clone", "--quiet", "--filter=blob:none", "--no-checkout", "--single-branch", url, dst)
        except subprocess.CalledProcessError as e2:
            return {"url": url, "skipped": f"clone failed: {str(e2.stderr)[-120:]}"}
    def last_before() -> str:
        try:
            # --first-parent: the default branch's OWN state. Plain rev-list returns the newest pre-cutoff
            # commit in any merged-in ancestry (protobuf gave a commit from the upb repository: no src/).
            return git("rev-list", "-1", "--first-parent", f"--before={CUTOFF}T00:00:00Z", "HEAD", cwd=dst)
        except subprocess.CalledProcessError:
            return ""
    commit = last_before()
    if not commit:      # quiet repo: nothing between the shallow-since date and the cutoff -> full history, lazy blobs
        _rmtree(dst)
        try:
            git("clone", "--quiet", "--filter=blob:none", "--no-checkout", "--single-branch", url, dst)
        except subprocess.CalledProcessError as e2:
            return {"url": url, "skipped": f"clone failed: {str(e2.stderr)[-120:]}"}
        commit = last_before()
    if not commit:
        return {"url": url, "skipped": "no commit before the cutoff in the full history"}
    date = git("show", "-s", "--format=%cI", commit, cwd=dst)
    git("checkout", "--quiet", commit, cwd=dst)
    lic, lic_file, note = classify_license(dst)
    if not lic:
        return {"url": url, "commit": commit, "commit_date": date, "skipped": f"licence: {note}"}
    parts, n_files, chars = [], 0, 0
    for dp, dns, fns in os.walk(dst):
        rel_d = os.path.relpath(dp, dst).replace("\\", "/")
        if SKIP_DIRS.search(rel_d + "/"):
            dns[:] = []; continue
        for fn in fns:
            if not fn.endswith(EXT[lang]) or SKIP_FILES.search(fn):
                continue
            p = os.path.join(dp, fn)
            try:
                if os.path.getsize(p) > 400_000:
                    continue
                text = io.open(p, encoding="utf-8", errors="strict").read()
            except (UnicodeDecodeError, OSError):
                continue
            if "\x00" in text or (len(text) > 2000 and max(len(l) for l in text.splitlines()[:200]) > 2000):
                continue
            rel = os.path.relpath(p, dst).replace("\\", "/")
            parts.append(f"// ==== {name}/{rel} ====\n" if lang != "python" else f"# ==== {name}/{rel} ====\n")
            parts.append(text.rstrip() + "\n\n")
            n_files += 1; chars += len(text)
    body = "".join(parts)
    return {"url": url, "name": name, "commit": commit, "commit_date": date, "license": lic, "license_file": lic_file,
            "license_note": note, "files": n_files, "characters": chars, "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "seconds": round(time.time() - t0, 1), "text": body}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=list(REPOS), default=None)
    ap.add_argument("--max-chars-per-repo", type=int, default=120_000_000)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    langs = [a.lang] if a.lang else list(REPOS)
    rows_path = os.path.join(OUT, "rows.json")
    rows = json.load(io.open(rows_path, encoding="utf-8")) if os.path.exists(rows_path) else {}
    for lang in langs:
        out_txt = os.path.join(OUT, f"{lang}.txt")
        done = {r["url"] for r in rows.get(lang, []) if "text" not in r and not r.get("skipped")}
        with io.open(out_txt, "a", encoding="utf-8", newline="\n") as f:
            for url in REPOS[lang]:
                if url in done:
                    continue
                tmp = tempfile.mkdtemp(prefix="dated_")
                try:
                    r = fetch_repo(url, lang, tmp)
                finally:
                    _rmtree(tmp)
                if r.get("skipped"):
                    print(f"  {lang} {url.rsplit('/',1)[-1]}: SKIPPED — {r['skipped']}", flush=True)
                else:
                    f.write(r.pop("text")[:a.max_chars_per_repo]); f.flush()
                    print(f"  {lang} {r['name']}: {r['files']:,} files, {r['characters']/1e6:.1f}M chars, {r['license']} ({r['license_file']}), {r['commit'][:10]} @ {r['commit_date'][:10]}, {r['seconds']}s", flush=True)
                rows[lang] = [x for x in rows.get(lang, []) if x["url"] != url] + [r]   # a retried skip replaces its row
                io.open(rows_path, "w", encoding="utf-8", newline="\n").write(json.dumps(rows, indent=1, ensure_ascii=False))
    for lang in langs:
        kept = [r for r in rows.get(lang, []) if not r.get("skipped")]
        print(f"{lang}: {len(kept)} repos kept, {sum(r['characters'] for r in kept)/1e6:.0f}M chars; skipped {len(rows.get(lang, [])) - len(kept)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build the 1B data volume (D-82, JOB_1B step 1): fetch dated shards, tokenize each, concatenate.

Every shard is fetched with the project's own ledger-writing fetchers (nothing enters without a
row), tokenized with tokenize_corpus.py (uint16, val spread), its raw text deleted, and the
tokenized shards are concatenated at the end into <out>/train.bin + val.bin + meta.json with a
per-shard table (slug, tokens, sha256 of the .bin) so the volume itself is auditable. Idempotent:
a shard whose tokenized meta.json exists is skipped, so the pod job can be resumed.

    python scripts/build_volume.py --plan plans/volume_1b.json --out /workspace/volume --workers 16
    python scripts/build_volume.py --plan plans/volume_smoke.json --out data/volume_smoke --workers 2   # desk test

Plan file: {"shards": [{"slug": ..., "kind": "fineweb"|"wikipedia"|"stackexchange"|"text",
                         ...kind-specific fields..., "target_tokens": N}]}
Kinds: fineweb  -> fetch_data.py --config <dump> --date-field dump --docs <docs>
       stackexchange -> fetch_stackexchange.py --docs <docs>
       wikipedia -> fetch_wikipedia_dump.py --target-chars <chars>
       text      -> an existing data/raw file (already ledgered), e.g. the dated code files
train.py samples random windows from the flat stream, so the mixture is set by token counts, and
a shard listed twice in the plan is an epoch (write it on the row).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
TOK = os.path.join(ROOT, "data", "tokenizer_real", "tokenizer.json")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str], log: str) -> None:
    print("  $ " + " ".join(cmd), flush=True)
    with io.open(log, "a", encoding="utf-8") as lf:
        r = subprocess.run(cmd, cwd=ROOT, stdout=lf, stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0:
        tail = io.open(log, encoding="utf-8", errors="replace").read()[-2000:]
        raise SystemExit(f"FAILED ({r.returncode}): {' '.join(cmd)}\n{tail}")


def fetch(shard: dict, raw: str, log: str) -> None:
    k = shard["kind"]
    if k == "fineweb":
        run([PY, "scripts/fetch_data.py", "--dataset", "HuggingFaceFW/fineweb-edu", "--config", shard["dump"],
             "--date-field", "dump", "--date-max", "CC-MAIN-2021-99", "--docs", str(shard["docs"]), "--out", raw], log)
    elif k == "stackexchange":
        run([PY, "scripts/fetch_stackexchange.py", "--docs", str(shard["docs"]), "--out", raw], log)
    elif k == "wikipedia":
        run([PY, "scripts/fetch_wikipedia_dump.py", "--target-chars", str(shard["chars"]), "--out", raw,
             "--seed", str(shard.get("seed", 1337))], log)
    elif k == "text":
        src = os.path.join(ROOT, shard["file"])
        if not os.path.exists(src):
            raise SystemExit(f"text shard missing: {src}")
        if os.path.abspath(src) != os.path.abspath(raw):
            shutil.copyfile(src, raw)
    else:
        raise SystemExit(f"unknown kind {k}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--val-fraction", type=float, default=0.002)
    ap.add_argument("--keep-raw", action="store_true")
    ap.add_argument("--only", default="", help="comma-separated shard slugs to build (default all)")
    ap.add_argument("--no-concat", action="store_true")
    a = ap.parse_args()
    plan = json.load(io.open(a.plan, encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)
    shards_dir = os.path.join(a.out, "shards")
    raw_dir = os.path.join(a.out, "raw")
    os.makedirs(shards_dir, exist_ok=True); os.makedirs(raw_dir, exist_ok=True)
    log = os.path.join(a.out, "build.log")
    only = {s for s in a.only.split(",") if s}
    table = []
    t_all = time.time()
    for shard in plan["shards"]:
        slug = shard["slug"]
        if only and slug not in only:
            continue
        tdir = os.path.join(shards_dir, slug)
        meta_p = os.path.join(tdir, "meta.json")
        if os.path.exists(meta_p):
            m = json.load(io.open(meta_p, encoding="utf-8"))
            print(f"  {slug}: done already ({m['train_tokens']:,} tokens)", flush=True)
            table.append({"slug": slug, **{k: m[k] for k in ("train_tokens", "val_tokens", "source_chars")}, "epochs": shard.get("epochs", 1)})
            continue
        t0 = time.time()
        raw = os.path.join(raw_dir, slug + ".txt")
        if not os.path.exists(raw):
            fetch(shard, raw, log)
        run([PY, "scripts/tokenize_corpus.py", "--input", raw, "--tokenizer", TOK, "--out", tdir,
             "--val-fraction", str(a.val_fraction), "--val-mode", "spread", "--workers", str(a.workers)], log)
        m = json.load(io.open(meta_p, encoding="utf-8"))
        m["sha256_train_bin"] = sha256_file(os.path.join(tdir, "train.bin"))
        m["sha256_raw"] = sha256_file(raw)
        m["shard"] = shard
        m["seconds"] = round(time.time() - t0, 1)
        io.open(meta_p, "w", encoding="utf-8", newline="\n").write(json.dumps(m, indent=1))
        if not a.keep_raw and shard["kind"] != "text":
            os.remove(raw)
        print(f"  {slug}: {m['train_tokens']:,} tokens in {m['seconds']}s", flush=True)
        table.append({"slug": slug, **{k: m[k] for k in ("train_tokens", "val_tokens", "source_chars")}, "epochs": shard.get("epochs", 1)})
    if a.no_concat:
        return 0
    # concatenate: a shard with epochs=N is written N times (an epoch is a repeat, on the record)
    total_train = total_val = 0
    with open(os.path.join(a.out, "train.bin"), "wb") as tb, open(os.path.join(a.out, "val.bin"), "wb") as vb:
        for row in table:
            tdir = os.path.join(shards_dir, row["slug"])
            for _ in range(int(row["epochs"])):
                with open(os.path.join(tdir, "train.bin"), "rb") as f:
                    shutil.copyfileobj(f, tb, 1 << 24)
                total_train += row["train_tokens"]
            with open(os.path.join(tdir, "val.bin"), "rb") as f:
                shutil.copyfileobj(f, vb, 1 << 24)
            total_val += row["val_tokens"]
    meta = {"tokenizer": os.path.relpath(TOK, ROOT).replace("\\", "/"), "vocab_size": 32768, "dtype": "uint16",
            "train_tokens": total_train, "val_tokens": total_val, "total_tokens": total_train + total_val,
            "shards": table, "built_seconds": round(time.time() - t_all, 1),
            "note": "concatenated shards; train.py samples random windows so the mixture is the token counts; epochs>1 = the shard repeated"}
    io.open(os.path.join(a.out, "meta.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(meta, indent=1))
    print(f"volume: {total_train:,} train tokens, {total_val:,} val tokens, {len(table)} shards -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

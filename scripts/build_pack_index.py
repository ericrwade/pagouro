"""Build packs/index.json: one embedding vector per pack chunk.

Run at package time (master_pipeline.sh stage 10) so the stick ships the vectors and
the app only has to embed the question. Uses llama-server with the bge-small
embedder (CompendiumLabs/bge-small-en-v1.5-gguf, MIT, 384 dims) on a private port.

    python scripts/build_pack_index.py --packs packs --embedder tools/embed/bge-small-en-v1.5-q8_0.gguf
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))
from packsearch import chunk_file  # noqa: E402


def pieces_of(text: str, limit: int = 60) -> list[str]:
    """Split a chunk into pieces of at most `limit` characters at sentence or word ends."""
    out, cur = [], ""
    for sent in re.split(r"(?<=[.!?;:])\s+", text):
        for word in sent.split():
            if len(cur) + 1 + len(word) > limit and cur:
                out.append(cur)
                cur = word
            else:
                cur = (cur + " " + word).strip()
    if cur:
        out.append(cur)
    return out or [text[:limit]]


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packs", default=os.path.join(ROOT, "packs"))
    ap.add_argument("--embedder", default=os.path.join(ROOT, "tools", "embed", "bge-small-en-v1.5-q8_0.gguf"))
    ap.add_argument("--server", default=os.path.join(ROOT, "tools", "llamacpp", "llama-server.exe"))
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()

    files = sorted(f for f in os.listdir(a.packs) if f.lower().endswith(".txt"))
    rows = []
    for fn in files:
        for ch in chunk_file(os.path.join(a.packs, fn)):
            rows.append({"file": fn, "text": ch})
    print(f"{len(rows)} chunks from {len(files)} files")

    port = free_port()
    proc = subprocess.Popen([a.server, "-m", a.embedder, "--embedding", "--port", str(port), "-ngl", "0",
                             "-t", str(a.threads), "--log-disable", "--no-webui", "-c", "512", "-b", "512", "-ub", "512"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(120):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2)
                break
            except Exception:
                time.sleep(0.25)
        t0 = time.time()

        def embed_batch(texts):
            req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/embeddings",
                                         data=json.dumps({"input": texts}).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            d = json.loads(urllib.request.urlopen(req, timeout=300).read())
            return [e["embedding"] for e in d["data"]]

        # This llama-server build crashes on embedding inputs past ~40 tokens (BERT and
        # NomicBERT alike, any quant; found 2026-09-18). So each chunk is embedded as
        # the mean of its short pieces (<= 100 chars, split at sentence ends), which is
        # a standard approximation and keeps every request inside the safe length.
        for i, r in enumerate(rows):
            pieces = pieces_of(r["text"])
            vecs = []
            for piece in pieces:                 # ONE piece per request: the limit is ~32 tokens per request
                vecs += embed_batch([piece])
            dims = len(vecs[0])
            mean = [sum(v[k] for v in vecs) / len(vecs) for k in range(dims)]
            norm = sum(x * x for x in mean) ** 0.5 or 1.0
            r["vec"] = [round(x / norm, 4) for x in mean]
            if i % 50 == 0:
                print(f"  {i}/{len(rows)}  {time.time() - t0:.0f}s", flush=True)
    finally:
        proc.terminate()

    dims = len(rows[0]["vec"]) if rows else 0
    index = {
        "model": os.path.basename(a.embedder),
        "model_sha256": hashlib.sha256(open(a.embedder, "rb").read()).hexdigest(),
        "dims": dims,
        "chunk_chars": 600,
        "files": files,
        "chunks": rows,
    }
    out = os.path.join(a.packs, "index.json")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(index, f, ensure_ascii=False)
    print(f"wrote {out}: {len(rows)} chunks x {dims} dims, {os.path.getsize(out) / 1e6:.1f} MB, {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

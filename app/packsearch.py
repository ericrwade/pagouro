"""Pack search shared by the app and scripts/build_pack_index.py.

Two tiers, so the stick works either way:
  - embedded: packs/index.json holds one vector per chunk (built at package time by
    scripts/build_pack_index.py with the bge-small embedder, MIT, 37 MB). At query
    time only the question is embedded, by a second llama-server process running the
    same embedder, and chunks are ranked by cosine similarity.
  - keyword: BM25 over the same chunks. Used when the index or the embedder is
    missing. Measured 2026-09-18: at least as good as the piecewise-averaged
    embeddings this llama-server build can produce (it crashes on embedding inputs
    past ~32 tokens), so BM25 is what the stick ships with; the index is optional.

The chunker lives here so the index and the live search can never disagree about
what a chunk is.
"""

from __future__ import annotations

import json
import math
import os
import re

STOP = {"the", "and", "that", "with", "for", "this", "what", "which", "from", "are", "was", "were",
        "have", "has", "not", "but", "his", "her", "its", "they", "them", "there", "their", "than",
        "then", "into", "upon", "about", "does", "did", "how", "why", "who", "can", "all", "any",
        "one", "two", "say", "says", "said", "does", "packs", "pack", "search", "reference", "text"}

CHUNK_CHARS = 600


def chunk_file(path: str) -> list[str]:
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    out, buf = [], []
    for para in re.split(r"\n\s*\n", text):
        para = " ".join(para.split())
        if not para:
            continue
        buf.append(para)
        if sum(len(p) for p in buf) >= CHUNK_CHARS:
            out.append(" ".join(buf))
            buf = []
    if buf:
        out.append(" ".join(buf))
    return out


def words(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{3,}", s.lower()) if w not in STOP}


def tokens(s: str) -> list[str]:
    return [w for w in re.findall(r"[a-z]{3,}", s.lower()) if w not in STOP]


class BM25:
    """Okapi BM25 over the chunks. Term-frequency saturation (k1) and length
    normalisation (b) are what the naive overlap score lacked: a footnote chunk that
    says "Mill" nine times no longer beats the passage that says "harm" once."""

    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tf: list[dict[str, int]] = []
        self.len: list[int] = []
        df: dict[str, int] = {}
        for d in docs:
            toks = tokens(d)
            counts: dict[str, int] = {}
            for t in toks:
                counts[t] = counts.get(t, 0) + 1
            self.tf.append(counts)
            self.len.append(len(toks))
            for t in counts:
                df[t] = df.get(t, 0) + 1
        n = max(1, len(docs))
        self.avg = (sum(self.len) / n) if docs else 1.0
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def score(self, query: str, i: int) -> float:
        counts, L = self.tf[i], self.len[i]
        s = 0.0
        for t in set(tokens(query)):
            f = counts.get(t)
            if not f:
                continue
            idf = self.idf.get(t, 0.0)
            s += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * L / self.avg))
        return s


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


class Packs:
    def __init__(self, root: str, embed=None):
        """embed: callable(str) -> list[float] or None. Supplied by the app when the
        embedder server is up; None means keyword-only."""
        self.root = root
        self.embed = embed
        self.names: list[str] = []
        self.chunks: list[tuple[str, str]] = []
        self.vectors: list[list[float]] | None = None
        self.index_model = None
        if not os.path.isdir(root):
            return
        index_path = os.path.join(root, "index.json")
        index = None
        if os.path.exists(index_path):
            try:
                with open(index_path, encoding="utf-8") as f:
                    index = json.load(f)
            except Exception:
                index = None
        if index and embed is not None:
            self.index_model = index.get("model")
            for row in index["chunks"]:
                self.chunks.append((row["file"], row["text"]))
                if row["file"] not in self.names:
                    self.names.append(row["file"])
            self.vectors = [row["vec"] for row in index["chunks"]]
        else:
            for fn in sorted(os.listdir(root)):
                if fn.lower().endswith(".txt"):
                    self.names.append(fn)
                    for ch in chunk_file(os.path.join(root, fn)):
                        self.chunks.append((fn, ch))

        self.bm25 = BM25([t for _, t in self.chunks])

    def add_dir(self, root: str, prefix: str) -> int:
        """Index every .txt in another folder under `prefix:filename` -- used for the owner's
        long-term memory (workspace/memory, notes, STONE transcripts), so what the user said in
        earlier sessions comes back by retrieval, labelled as theirs (O-23). Keyword mode only;
        the embedded index, if any, covers the packs alone. Returns chunks added."""
        if not os.path.isdir(root):
            return 0
        n = 0
        for fn in sorted(os.listdir(root)):
            if fn.lower().endswith(".txt"):
                name = f"{prefix}:{fn}"
                if name in self.names:
                    continue
                self.names.append(name)
                # Memory is one entry per paragraph, never merged: a remembered line must be its own
                # hit, or a small model reads the first line of a merged chunk for every question.
                with open(os.path.join(root, fn), encoding="utf-8", errors="replace") as f:
                    for para in re.split(r"\n\s*\n", f.read()):
                        para = " ".join(para.split())
                        if para:
                            self.chunks.append((name, para[:CHUNK_CHARS * 2]))
                            n += 1
        if n:
            self.vectors = None                      # mixed corpus: fall back to BM25 for everything
            self.bm25 = BM25([t for _, t in self.chunks])
        return n

    def reindex_dir(self, root: str, prefix: str) -> int:
        """Drop everything under `prefix:` and index the folder again (after a /remember)."""
        keep = [(n, t) for n, t in self.chunks if not n.startswith(prefix + ":")]
        self.chunks = keep
        self.names = [n for n in self.names if not n.startswith(prefix + ":")]
        added = self.add_dir(root, prefix)
        if not added:
            self.bm25 = BM25([t for _, t in self.chunks])
        return added

    @property
    def mode(self) -> str:
        return "embedded" if self.vectors is not None else "keyword"

    def search(self, query: str, k: int = 3) -> list[tuple[str, str, float]]:
        if not self.chunks:
            return []
        q = words(query)
        if self.vectors is not None and self.embed is not None:
            try:
                qv = self.embed(query)
            except Exception:
                qv = None
            if qv:
                scored = []
                for (name, text), vec in zip(self.chunks, self.vectors):
                    s = cosine(qv, vec)
                    if q:
                        s += 0.02 * len(q & words(text))      # small keyword tie-breaker
                    scored.append((s, name, text))
                scored.sort(reverse=True)
                return [(n, t, s) for s, n, t in scored[:k]]
        if not q:
            return []
        scored = [(self.bm25.score(query, i) * (1.25 if name.startswith("memory:") else 1.0), name, text)
                  for i, (name, text) in enumerate(self.chunks)]   # the owner's own words win near-ties
        scored = [x for x in scored if x[0] > 0]
        scored.sort(reverse=True)
        return [(n, t, s) for s, n, t in scored[:k]]

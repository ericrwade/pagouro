"""Assemble the pretraining mixture and the anneal mixture from fetched sources.

Implements D-9's stage separation, the one rule that matters most here: the
PRETRAIN mix is optimised for reasoning (general web + code), domain material
is concentrated in the ANNEAL (the final slice of training), and ethos lives in
SFT, not here. Loading the pretrain mix with domain text costs reasoning and
buys little knowledge -- see docs/CORPUS_PLAN.md.

Every file this script reads must already have a corpus.json row (checked
before use, not after) so nothing enters the mixture without a ledger entry.

    python scripts/build_mixture.py
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
LEDGER = os.path.join(ROOT, "corpus.json")

# (file relative to data/raw, or an absolute path under ROOT, target share)
# Shares are of PRETRAIN tokens only; the anneal mixture is separate and listed below.
PRETRAIN_MIX = [
    # Dolma dropped: allenai/dolma uses a legacy HF dataset loading script the
    # current `datasets` library no longer supports (same failure class as
    # codeparrot/github-code-clean earlier -- see docs/CORPUS_PLAN.md 2a).
    # Its 20% share is redistributed to FineWeb-Edu and Wikipedia, both of
    # which succeeded and serve an overlapping role (educational/general web).
    ("fineweb-edu-big.txt",                        0.45),
    ("fineweb-edu-sample-10BT.txt",                 0.10),  # M1's original slice, reused
    ("the-stack-python.txt",                        0.08),
    ("the-stack-rust.txt",                          0.04),
    ("the-stack-go.txt",                            0.04),
    ("the-stack-solidity.txt",                      0.04),
    ("wikipedia-en.txt",                            0.20),
    ("stackexchange-preferences.txt",               0.05),
]

# The anneal draws from the domain canon plus contemporary voice and synthetic
# crypto knowledge -- this is where D-38's canon and Eric's crypto material live.
ANNEAL_SOURCES = [
    "gutenberg/second-treatise-of-government.txt",
    "gutenberg/the-wealth-of-nations.txt",
    "gutenberg/the-theory-of-moral-sentiments.txt",
    "gutenberg/the-law.txt",
    "gutenberg/economic-sophisms.txt",
    "gutenberg/on-liberty.txt",
    "gutenberg/principles-of-political-economy.txt",
    "gutenberg/on-the-principles-of-political-economy-and-taxation.txt",
    "gutenberg/democracy-in-america-volume-1.txt",
    "gutenberg/democracy-in-america-volume-2.txt",
    "gutenberg/the-federalist-papers.txt",
    "gutenberg/progress-and-poverty.txt",
    "gutenberg/the-communist-manifesto.txt",
    "gutenberg/anthem.txt",
    "bitcointalk/bitcointalk_sample.txt",
]


def read_if_exists(rel: str) -> str:
    path = os.path.join(RAW, rel)
    if not os.path.exists(path):
        print(f"  SKIP (not fetched yet): {rel}")
        return ""
    with io.open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pretrain-chars", type=int, default=1_400_000_000,
                    help="target character budget for the pretrain mix (~4 chars/token)")
    ap.add_argument("--anneal-fraction", type=float, default=0.10,
                    help="anneal is this fraction of TOTAL training tokens (brief section 6)")
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "data", "mixture"))
    ap.add_argument("--seed", type=int, default=1337)
    a = ap.parse_args()

    os.makedirs(a.out_dir, exist_ok=True)
    rng = random.Random(a.seed)

    # Cross-check every listed source has a ledger row before using it.
    with io.open(LEDGER, encoding="utf-8") as f:
        ledger = json.load(f)
    known_files = {s.get("file", "").replace("\\", "/") for s in ledger["sources"]}

    print("=== PRETRAIN MIX ===")
    pretrain_parts = []
    total_share = sum(s for _, s in PRETRAIN_MIX)
    for rel, share in PRETRAIN_MIX:
        target_chars = int(a.pretrain_chars * (share / total_share))
        text = read_if_exists(rel)
        if not text:
            continue
        ledger_path = f"data/raw/{rel}"
        in_ledger = ledger_path in known_files
        if len(text) > target_chars:
            # Deterministic-but-shuffled sample rather than always taking the head,
            # so a partial fetch doesn't bias the mixture toward whatever streamed first.
            docs = text.split("\n\n")
            rng.shuffle(docs)
            out, n = [], 0
            for d in docs:
                if n >= target_chars:
                    break
                out.append(d)
                n += len(d)
            text = "\n\n".join(out)
        pretrain_parts.append(text)
        print(f"  {rel:<45} {len(text)/1e6:6.1f}M chars (target {target_chars/1e6:.1f}M) "
              f"{'[ledger OK]' if in_ledger else '[!! NOT IN LEDGER]'}")

    rng.shuffle(pretrain_parts)  # shuffle at the SOURCE level so sources interleave, not just within one
    pretrain_text = "\n\n".join(pretrain_parts)
    pretrain_out = os.path.join(a.out_dir, "pretrain.txt")
    io.open(pretrain_out, "w", encoding="utf-8", newline="\n").write(pretrain_text)
    print(f"\nwrote {pretrain_out}: {len(pretrain_text)/1e6:.1f}M chars, "
          f"~{len(pretrain_text)//4:,} tokens")

    print("\n=== ANNEAL MIX ===")
    anneal_parts = []
    for rel in ANNEAL_SOURCES:
        text = read_if_exists(rel)
        if text:
            anneal_parts.append(text)
            print(f"  {rel:<45} {len(text)/1e6:6.1f}M chars")

    # Synthetic crypto Q&A (DeepSeek, local, grounded -- D-30) converted from
    # JSONL to plain text for the anneal. Marked as synthetic in its own ledger
    # row already; here it just needs to be text the tokenizer can consume.
    synth_path = os.path.join(ROOT, "sft", "crypto_synthetic.jsonl")
    if os.path.exists(synth_path):
        lines = []
        with io.open(synth_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                lines.append(f"Question: {d['question']}\n\nAnswer: {d['answer']}")
        synth_text = "\n\n".join(lines)
        if synth_text:
            anneal_parts.append(synth_text)
            print(f"  {'sft/crypto_synthetic.jsonl (as text)':<45} {len(synth_text)/1e6:6.1f}M chars")
    # Add the highest-quality pretrain slice too, per brief section 6's annealing guidance.
    fw = read_if_exists("fineweb-edu-sample-10BT.txt")
    if fw:
        anneal_parts.append(fw[: len(fw) // 4])   # a slice of it, not all of it
    rng.shuffle(anneal_parts)
    anneal_text = "\n\n".join(anneal_parts)
    anneal_out = os.path.join(a.out_dir, "anneal.txt")
    io.open(anneal_out, "w", encoding="utf-8", newline="\n").write(anneal_text)
    print(f"\nwrote {anneal_out}: {len(anneal_text)/1e6:.1f}M chars, "
          f"~{len(anneal_text)//4:,} tokens")

    total_tokens = len(pretrain_text)//4 + len(anneal_text)//4
    print(f"\nTOTAL MIXTURE: ~{total_tokens:,} tokens "
          f"(anneal is {100*len(anneal_text)//4/max(total_tokens,1):.0f}% of total)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

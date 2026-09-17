"""Generate synthetic crypto Q&A pairs using a LOCAL open-weights DeepSeek model.

D-30 is absolute: synthetic training data comes from open weights run locally,
never from an API. This script runs `bartowski/DeepSeek-R1-Distill-Qwen-7B-GGUF`
(MIT license, Apache-2.0 base -- verified against the source model card) via
llama.cpp on this machine. No network call happens during generation.

GROUNDING, not free generation: a smoke test showed the 1.5B distill state
UTXO mechanics incorrectly when asked to explain freely from its own memory.
Rather than trust an unverified model's parametric recall for the exact
subject matter this project claims to handle honestly, every passage in
sft/crypto_source_passages.py is hand-written and checked, and the model's
job is narrowed to producing a well-framed Q&A pair FROM a given true
passage -- extraction and rephrasing, not authorship of facts.

DeepSeek-R1-distill models "think" in a visible block before answering, and
will burn an entire small token budget on that thinking alone, returning no
usable answer. Generous per-call token budget is deliberate; parsing takes
everything after the LAST "[End thinking]" marker.

    python scripts/generate_synthetic_crypto.py
    python scripts/generate_synthetic_crypto.py --limit 5   # smoke test
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "sft"))
from crypto_source_passages import PASSAGES  # noqa: E402

MODEL = os.path.join(ROOT, "data", "models", "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf")
LLAMA_CHAT = os.path.join(ROOT, "tools", "llamacpp", "llama-cli.exe")
OUT = os.path.join(ROOT, "sft", "crypto_synthetic.jsonl")
ANSI = re.compile("\x1b\\[[0-9;]*m")

PROMPT_TMPL = """Based ONLY on the following true passage, write ONE clear question a curious \
beginner might ask, and a direct answer using ONLY facts from the passage. Do not add any \
outside information. Do not repeat the passage verbatim; explain it in your own words.

Passage: "{passage}"

Reply in exactly this format, nothing else after it:
Q: <question>
A: <answer>"""


def extract_answer(raw: str) -> str:
    """Everything after the LAST 'End thinking' marker is the real answer.
    Falls back to the raw text if the model didn't emit a thinking block."""
    txt = ANSI.sub("", raw)
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    markers = ["[End thinking]", "[end of thinking]", "</think>"]
    best = None
    for m in markers:
        i = txt.rfind(m)
        if i >= 0:
            candidate = txt[i + len(m):]
            if best is None or i > txt.rfind(best[1]):
                best = (candidate, m)
    tail = best[0] if best else txt
    tail = re.split(r"\n\s*\[end of text\]|\nllama_perf|\nExiting|> |\[ Prompt:", tail)[0]
    return tail.strip()


def parse_qa(text: str) -> tuple[str, str] | None:
    m = re.search(r"Q:\s*(.+?)\s*\nA:\s*(.+)", text, re.DOTALL)
    if not m:
        return None
    q = re.sub(r"\s+", " ", m.group(1)).strip()
    a = re.sub(r"\s+", " ", m.group(2)).strip()
    if len(q) < 8 or len(a) < 15:
        return None
    return q, a


def generate_one(passage: str, n_tokens: int, timeout: int) -> str:
    prompt = PROMPT_TMPL.format(passage=passage)
    cmd = [LLAMA_CHAT, "-m", MODEL, "-p", prompt, "-st", "-n", str(n_tokens),
          "--temp", "0.3", "--seed", "7", "--no-warmup", "-ngl", "0"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                             encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return ""
    return extract_answer(res.stdout or "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokens", type=int, default=900)
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()

    if not os.path.exists(MODEL):
        raise SystemExit(f"missing model: {MODEL}")
    if not os.path.exists(LLAMA_CHAT):
        raise SystemExit(f"missing llama-cli: {LLAMA_CHAT}")

    passages = PASSAGES[: a.limit] if a.limit else PASSAGES
    print(f"generating from {len(passages)} grounded passages, "
          f"model=DeepSeek-R1-Distill-Qwen-7B (local, MIT), {a.tokens} tokens/call")

    results = []
    failed = []
    t0 = time.time()
    for i, (slug, passage) in enumerate(passages, 1):
        raw = generate_one(passage, a.tokens, a.timeout)
        qa = parse_qa(raw)
        el = time.time() - t0
        if qa:
            q, ans = qa
            results.append({
                "source_slug": slug, "passage": passage,
                "question": q, "answer": ans,
                "generator": "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M (local, MIT license)",
                "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
            print(f"  [{i:2d}/{len(passages)}] {slug:<30} OK   ({el:5.0f}s elapsed)", flush=True)
        else:
            failed.append(slug)
            print(f"  [{i:2d}/{len(passages)}] {slug:<30} FAILED to parse Q/A "
                  f"({el:5.0f}s elapsed)", flush=True)
            if raw:
                print(f"      raw tail: {raw[:150]!r}")

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nwrote {os.path.relpath(OUT, ROOT)}: {len(results)}/{len(passages)} succeeded")
    if failed:
        print(f"failed slugs: {failed}")
    print(f"total time: {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

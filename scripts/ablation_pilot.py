"""M4 ablation pilot: does adding a code slice measurably change a small model?

This is a METHODOLOGY pilot, not a result. At ~12M parameters on ~6M tokens the
finding carries no weight whatever it says. What is being tested is whether the
comparison machinery is sound: same tokenizer, same token budget, same seed, same
config, one variable changed.

Controls, each of which would otherwise be a confound:
  - ONE tokenizer, trained on both corpora combined, used by both runs. Training
    separate tokenizers would change the token boundaries and make perplexity
    incomparable.
  - IDENTICAL total token count. Run B does not get more data, it gets different
    data in place of some.
  - IDENTICAL seed, config, learning-rate schedule and step count.

    python scripts/ablation_pilot.py --steps 1500
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
AB = os.path.join(ROOT, "data", "ablation")


def sh(cmd: list[str], **kw) -> int:
    print("  $", " ".join(str(c) for c in cmd[:6]), "...", flush=True)
    return subprocess.run(cmd, cwd=ROOT, **kw).returncode


def fetch_code(target_chars: int) -> str:
    """Rosetta Code: GFDL, not gated, streams without authentication.

    PILOT ONLY. GFDL is share-alike, so this source falls under O-11 and is not a
    candidate for the real corpus. It is used here because every permissively
    licensed code corpus checked was either gated (the whole BigCode family) or
    built on a loading script the current datasets library no longer supports.
    See docs/CORPUS_PLAN.md 2a.
    """
    from datasets import load_dataset
    out = os.path.join(AB, "code.txt")
    if os.path.exists(out) and os.path.getsize(out) > target_chars * 0.8:
        print(f"  code corpus already present ({os.path.getsize(out)/1e6:.1f} MB)")
        return out
    os.makedirs(AB, exist_ok=True)
    ds = load_dataset("christopher/rosetta-code", split="train", streaming=True)
    n = 0
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        for row in ds:
            code = (row.get("code") or "").strip()
            if len(code) < 40:
                continue
            desc = (row.get("task_description") or "").strip()
            lang = (row.get("language_name") or "").strip()
            if desc:
                f.write(f"# Task: {row.get('task_name','')} ({lang})\n# {desc[:400]}\n")
            f.write(code + "\n\n")
            n += len(code)
            if n >= target_chars:
                break
    print(f"  code corpus: {n/1e6:.1f}M chars")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--code-share", type=float, default=0.15)
    ap.add_argument("--vocab", type=int, default=8192)
    a = ap.parse_args()

    os.makedirs(AB, exist_ok=True)
    web_src = os.path.join(ROOT, "data", "raw", "fineweb-edu-sample-10BT.txt")
    if not os.path.exists(web_src):
        raise SystemExit("run scripts/fetch_data.py first")

    web = io.open(web_src, encoding="utf-8").read()
    print(f"web corpus: {len(web)/1e6:.1f}M chars")

    code_path = fetch_code(int(len(web) * a.code_share * 1.3))
    code = io.open(code_path, encoding="utf-8").read()

    # Corpus A: web only. Corpus B: same size, with code substituted for a slice.
    n_code = int(len(web) * a.code_share)
    n_code = min(n_code, len(code))
    corpus_a = web
    corpus_b = web[: len(web) - n_code] + "\n\n" + code[:n_code]
    print(f"corpus A (web only)      : {len(corpus_a)/1e6:.1f}M chars")
    print(f"corpus B (web + {a.code_share:.0%} code): {len(corpus_b)/1e6:.1f}M chars "
          f"({n_code/1e6:.1f}M of it code)")
    assert abs(len(corpus_a) - len(corpus_b)) < len(corpus_a) * 0.01, "corpora must match in size"

    for name, text in (("a_web", corpus_a), ("b_code", corpus_b)):
        io.open(os.path.join(AB, f"{name}.txt"), "w", encoding="utf-8", newline="\n").write(text)

    # ONE tokenizer for both, trained on a combined sample.
    tok_dir = os.path.join(AB, "tokenizer")
    if not os.path.exists(os.path.join(tok_dir, "tokenizer.json")):
        combined = os.path.join(AB, "combined.txt")
        io.open(combined, "w", encoding="utf-8", newline="\n").write(
            web[: len(web)//2] + "\n\n" + code[: n_code])
        print("\ntraining the shared tokenizer on a combined sample")
        if sh([PY, "scripts/train_tokenizer.py", "--input", combined,
               "--vocab-size", str(a.vocab), "--out", tok_dir]):
            return 1
        os.remove(combined)

    results = {}
    for name in ("a_web", "b_code"):
        print(f"\n=== arm {name} ===", flush=True)
        tok_out = os.path.join(AB, f"tokenized_{name}")
        if not os.path.exists(os.path.join(tok_out, "meta.json")):
            if sh([PY, "scripts/tokenize_corpus.py",
                   "--input", os.path.join(AB, f"{name}.txt"),
                   "--tokenizer", os.path.join(tok_dir, "tokenizer.json"),
                   "--out", tok_out]):
                return 1
        meta = json.load(io.open(os.path.join(tok_out, "meta.json"), encoding="utf-8"))
        print(f"  tokens: {meta['total_tokens']:,}")

        ck = os.path.join(ROOT, "checkpoints", f"ablation_{name}.pt")
        log = os.path.join(ROOT, "runs", f"ablation_{name}.jsonl")
        if os.path.exists(log):
            os.remove(log)
        if sh([PY, "-u", "scripts/train.py", "--max-steps", str(a.steps),
               "--eval-every", "250", "--ckpt-every", str(a.steps), "--seed", "1337",
               "--data-dir", tok_out, "--ckpt", ck, "--log", log]):
            return 1
        results[name] = {"tokens": meta["total_tokens"]}

    print("\nPILOT COMPLETE. Read runs/ablation_*.jsonl for the loss curves.")
    print("Reminder: at this scale the FINDING is meaningless. The METHOD is the deliverable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Train a byte-level BPE tokenizer and write it in Hugging Face format.

Vocabulary stays under 65,536 (DECISIONS.md D-7) for two independent reasons:
the embedding table would otherwise eat a large share of a 1B parameter budget,
and token ids fit in uint16, which halves both tokenized corpus size on disk and
data-loader bandwidth on every epoch. D-33 sets the real-run default at ~32,768
and requires DIGIT SPLITTING: each digit gets its own token, via a Digits
pre-tokenizer composed before ByteLevel. A BPE trainer left to its own devices
merges common multi-digit sequences into single tokens, which forces a model to
memorize arithmetic on arbitrary chunks rather than learn consistent positional
structure -- the one tokenizer choice D-33 identifies as having a measurable
effect on numerical reasoning.

Chat and tool-call tokens are present from day one so the chat template and the
tool harness never need a tokenizer change later. ChatML markup is used because
llama.cpp understands it without special handling.

Usage:
    python scripts/train_tokenizer.py --vocab-size 32768 --input data/raw/mixture.txt
"""

from __future__ import annotations

import argparse
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_INPUT = os.path.join(ROOT, "data", "raw", "fineweb-edu-sample-10BT.txt")
OUT_DIR = os.path.join(ROOT, "data", "tokenizer")

# Kept in one place so the trainer, the exporter and the harness cannot drift apart.
SPECIAL_TOKENS = [
    "<|endoftext|>",     # id 0: BOS, EOS and padding
    "<|im_start|>",      # chat turn open
    "<|im_end|>",        # chat turn close
    "<|tool_call|>",     # model requests a tool
    "<|tool_result|>",   # harness returns a result
    "<|unknown|>",
]

CHAT_TEMPLATE = (
    "{% for message in messages %}"
    "{{ '<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n' }}"
    "{% endfor %}"
    "{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=DEFAULT_INPUT)
    ap.add_argument("--vocab-size", type=int, default=32768)
    ap.add_argument("--out", default=OUT_DIR)
    a = ap.parse_args()

    if a.vocab_size > 65535:
        raise SystemExit(
            f"REFUSED: vocab-size {a.vocab_size} exceeds 65,535 and breaks the uint16 "
            "storage assumption. See DECISIONS.md D-7."
        )
    if not os.path.exists(a.input):
        raise SystemExit(f"input not found: {a.input}\nRun scripts/fetch_data.py first.")

    from tokenizers import Tokenizer, models, trainers, pre_tokenizers, decoders

    os.makedirs(a.out, exist_ok=True)

    tok = Tokenizer(models.BPE(unk_token=None))
    # D-33: Digits(individual_digits=True) runs BEFORE ByteLevel, splitting any run of
    # digits into single characters so the BPE trainer can never merge them back into
    # a multi-digit token. Order matters -- Sequence applies pre-tokenizers in order.
    tok.pre_tokenizer = pre_tokenizers.Sequence([
        pre_tokenizers.Digits(individual_digits=True),
        pre_tokenizers.ByteLevel(add_prefix_space=False),
    ])
    tok.decoder = decoders.ByteLevel()

    trainer = trainers.BpeTrainer(
        vocab_size=a.vocab_size,
        special_tokens=SPECIAL_TOKENS,
        show_progress=True,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
    )

    size_mb = os.path.getsize(a.input) / 1e6
    print(f"training BPE on {a.input} ({size_mb:.1f} MB), target vocab {a.vocab_size:,}")
    tok.train([a.input], trainer)

    tok_path = os.path.join(a.out, "tokenizer.json")
    tok.save(tok_path)

    # Minimal Hugging Face wrapper so llama.cpp's converter and transformers both
    # read the same tokenizer, including the chat template.
    cfg = {
        "tokenizer_class": "PreTrainedTokenizerFast",
        "model_max_length": 4096,
        "bos_token": "<|endoftext|>",
        "eos_token": "<|endoftext|>",
        "pad_token": "<|endoftext|>",
        "unk_token": None,
        "clean_up_tokenization_spaces": False,
        "chat_template": CHAT_TEMPLATE,
        "added_tokens_decoder": {
            str(i): {
                "content": t,
                "special": True,
                "lstrip": False, "rstrip": False,
                "normalized": False, "single_word": False,
            }
            for i, t in enumerate(SPECIAL_TOKENS)
        },
    }
    with io.open(os.path.join(a.out, "tokenizer_config.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
        f.write("\n")

    actual = tok.get_vocab_size()
    print(f"\nwrote {tok_path}")
    print(f"  vocabulary : {actual:,}")
    print(f"  uint16 safe: {actual <= 65535}")
    for t in SPECIAL_TOKENS:
        print(f"  {t:<16} -> id {tok.token_to_id(t)}")

    # Round-trip check. A tokenizer that does not round-trip silently corrupts the corpus.
    probe = "The hermit crab carries a home it did not build. 0x1F @ 3.14 -- éà中文"
    ids = tok.encode(probe).ids
    back = tok.decode(ids)
    ok = back == probe
    print(f"\nround-trip : {'PASS' if ok else 'FAIL'}  ({len(ids)} tokens for {len(probe)} chars)")
    if not ok:
        print(f"  original : {probe!r}")
        print(f"  decoded  : {back!r}")
        return 1

    # D-33 digit-splitting check: "12345" must decode to 5 separate digit tokens,
    # never one or two multi-digit merges. This is the tokenizer choice with an
    # actual measured effect on arithmetic; verify it rather than trust the config.
    digits = "12345"
    dig_ids = tok.encode(digits).ids
    dig_toks = [tok.id_to_token(i) for i in dig_ids]
    digits_ok = dig_toks == list(digits)
    print(f"digit split: {'PASS' if digits_ok else 'FAIL'}  {digits!r} -> {dig_toks}")
    if not digits_ok:
        print("  REFUSED: digits are not being split individually. Check pre_tokenizer order.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

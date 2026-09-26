---
license: cc-by-sa-4.0
language:
  - en
library_name: gguf
pipeline_tag: text-generation
tags:
  - pagouro
  - offline
  - licensed-corpus
  - pre-2022
  - honesty-measured
  - from-scratch
---

<!-- Draft 2, 2026-09-25 (O-43; honesty numbers and decode row filled from facts.json / D-93). Source for the Hugging Face model card at F10. Every TBD is filled
from a measured file at release (facts.json names the file per field). Wording bound by D-34
(the dated claim, exactly), D-50 (never "does not hallucinate"; bluff rate beside answered-real),
D-83 (no watermark, no claim on outputs) and THREAT_MODEL.md. -->

# Pagouro 1B

**An offline language model on a USB stick, built from scratch on a licensed, dated corpus, that
tells you when it does not know.** It is about a thousandth the size of the models you already use
and it loses to them on every capability test. What it offers is a set of promises a stranger can
check; the checks ship with it.

Made by Eric Wade, with Claude (Anthropic).

## The two numbers

On the frozen 100-item honesty sets (written before this model existed; `evals/`):

| | Pagouro 1B | small open models | frontier models |
|---|---|---|---|
| Invents an answer to a question that has none (**bluff rate**, lower is better) | **22 %** | 50–57 % | 23–27 % |
| Answers a real question correctly (**answered-real**, higher is better) | **81 %** | 87–93 % | 97 % |

Both numbers always appear together: a model that says nothing would score perfectly on the first
alone. Pagouro does not claim that it never hallucinates — no language model can — it claims to have
measured how often, and to ship the test so you can run it on this model and on any other.

## The dated claim, exactly

Every source in the training corpus was collected or published before **1 January 2022**, before
generative AI became widely available. Dump dates and publication dates are recorded per source in
the ledger (`corpus.json`). This is *not* a claim that the corpus is free of machine-generated
text: a crawl date is when a page was fetched, not when it was written.

## What it was trained on

| | |
|---|---|
| Tokens | 99,724,809,408 (pretraining), then a short decay on a mix with a licensed "shelf" of 31 works |
| Mixture | FineWeb-Edu (ODC-By, dumps ≤ CC-MAIN-2021-49) 91.6 % · Stack Exchange (CC BY-SA) 7.7 % · code from named repositories at their last commit before 2022-01-01, permissive licences only, ×3 0.7 % |
| Ledger | `corpus.json`: source, licence, date basis, token count, SHA-256 of the processed slice, per row; rows that were removed stay in it, marked, with the reason |
| Not in it | Wikipedia (dropped during the build, D-84); anything under a licence that could not be named; forum text without a date; anything first published in 2022 or later |

## Model

| | |
|---|---|
| Parameters | 968,968,192 (counted by the training script; "1B" means this and never more) |
| Architecture | decoder-only transformer, 20 layers, dim 2048, 16 heads / 4 KV heads, FFN 5,632, RoPE |
| Context | 8,192 tokens (trained at 4,096, extended to 8,192 for the decay phase, D-81) |
| Tokenizer | 32,768-entry BPE trained on the licensed corpus |
| Training | 8× H100 SXM (rented, RunPod, Montreal), 2026-09-22 → 09-24, 95,104 steps at 460k tokens/s; warmup-stable-decay schedule; bill $1,778.97 read from the account after the pod was deleted |
| Post-training | supervised fine-tune on the project's own seeds (abstention, tools, memory, style; `sft/`), then GRPO against the project's own honesty scorer (three rounds, `scripts/train_grpo.py`); no distillation from any other model |
| Files | `pagouro-q8_0.gguf` 1,102,230,720 bytes, SHA-256 `40f9907593c3e4ff95ee07a1e55ca5fe112d25ff8e82163600dbcd2a2bf4e0a1` — the file the app runs (the numbers above are measured on it); `pagouro-q4_k_m.gguf` 633,976,000 bytes, SHA-256 `7ea8fc4d5c23740097613d9cf8d74dd54a4957b34828ef2eb3936f7c6e2d3b52` ships beside it; the f32 export and the base (pre-SFT) model are published as their own artefacts at release |
| Decode | llama.cpp on CPU, 8,192-token context, greedy (temperature 0), no repetition penalty; a search result is shown to the model as at most 2 hits of 350 characters; a looping tail is cut at the first repeated sentence and the cut is announced. The two numbers above are measured at exactly these settings (D-93). Sampling at 0.3 measured 37 % / 76 % on the same model |

## Licence

Weights **CC BY-SA 4.0** — share-alike sources are in the corpus and the weights say so (D-31).
Code Apache 2.0. The project claims **no rights in what the model writes for you**, and there is
**no watermark** in its output: the program that produces every word is in the repository.

## Intended use, and what "private" means

Runs on any 64-bit machine on CPU, with no internet, no account, no update check and no telemetry.
`THREAT_MODEL.md` (shipped) says exactly what that protects against and where it stops; this card
claims nothing beyond it. Not for: anything where a wrong answer is dangerous and unchecked. It is
small, it is wrong often, and its whole design is that it tells you when it is unsure.

## Verify your copy

`MANIFEST.md` lists every shipped file with its SHA-256; its own hash is signed (`.minisig`) and
timestamped on Bitcoin (`.ots`). `CHECK_YOUR_COPY.md` walks a non-technical reader through the
check. A copy that does not match the manifest is not Pagouro.

## Finished

Released once and frozen. There is no roadmap, no support channel and no maintenance promise; the
only promise is that this file will keep being what it was when its hash was anchored. Fork it —
the corpus ledger, the training code and the book of how it was built are all in the repository.

## Relatives

OLMo (AI2) and the Common Pile / Comma models (EleutherAI) are larger, more capable, fully open
research models. Pagouro is the smaller relative that is also dated, measured for honesty first and
frozen; it borrows gratefully from both where their sources meet its rules.

## Citation

TBD at release (Zenodo/DOI or the GitHub Release tag `v1.0`).

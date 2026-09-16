# Pagouro

> A small language model, built from scratch, that lives on a USB stick and needs nothing from
> outside.
>
> Greek *págouros*, hermit crab: carries a home it can move out of. The *ouro* nods to ouroboros —
> self-sufficient.

**Status: milestone 1 of 9 complete.** This is a working end-to-end pipeline at toy scale, not the
model. Nothing here is released, and the numbers below are from a 12.6M parameter model trained for
31 minutes. See `docs/MILESTONES.md` for where this is going.

---

## What Pagouro will be

A ~1B parameter model, pretrained from random weights on a fully open and fully documented corpus,
packaged as a portable application that runs offline on any machine. Three properties define it:

- **It does not bluff.** It says "I don't know" rather than inventing an answer, and that is
  measured and published, not asserted.
- **Every training byte is accounted for** in `corpus.json`: source, licence, token count, and the
  hash of the processed slice. Anyone can check it; anyone could rebuild the corpus from it.
- **The person using it can ask anything**, because the conversation never leaves their machine.
  What that does and does not protect against is written down in `docs/THREAT_MODEL.md`, which
  governs what this README is allowed to claim.

It will be released as a finished artifact — signed, hash-anchored, licensed openly, with no
maintenance promise — and as a template others can fork into models built around other traditions.

## Read these first

| File | What it is |
|---|---|
| `START_HERE.md` | Session opener and current state |
| `docs/DECISIONS.md` | **Highest authority.** Every locked decision, with reasons |
| `PAGOURO_BRIEF.md` | Origin document. Partly superseded; carries a precedence notice |
| `docs/THREAT_MODEL.md` | Binding on every privacy claim |
| `docs/MILESTONES.md` | The nine milestones and their acceptance criteria |
| `ENVIRONMENT.md` | Hardware findings and measured baselines |

## Milestone 1 results

Trained on a 20,000-document slice of FineWeb-Edu (ODC-By), on CPU, on a GMKtec EVO-X2.

| | |
|---|---|
| Model | 12.6M parameters, dim 384, 6 layers, 6 heads, 2 KV heads |
| Corpus | 24.5M tokens, 8,192-token vocabulary |
| Training | 2,200 steps, 9.0M tokens, ~35 min on CPU at ~4,400 tok/s |
| Train loss | 9.084 → 4.879 |
| Validation perplexity | ~8,800 → **133.7** |
| GGUF export | 63.2 MB f32, **17.0 MB Q8_0** |
| Generation speed | **2,868 tok/s** on CPU, Q8, single-threaded prompt |

What it actually proves:

1. **The architecture converts.** Our own transformer exports to GGUF and llama.cpp loads it. This
   was the one-way door: an architecture llama.cpp cannot load is a model nobody can run.
2. **The export is faithful.** PyTorch and llama.cpp greedily decode the same prompt to *identical*
   text, 94 of 94 characters. "It converted" is not evidence; this is.
3. **Resume works.** Proven by killing a run at step 2100 and restarting it. Loss continued at 4.80
   rather than jumping back to 9.0, and the optimizer state came back with it.
4. **The chat template round-trips**, embedded in the GGUF rather than only in a side file.
5. **The ledger works.** `fetch_data.py` refuses any source without a licence on record.

The model itself is incoherent, which is correct at this size with no fine-tuning. It produces
grammatical English and repeats itself.

## Running it

Requires Python 3.12 and about 1 GB of disk. No GPU needed.

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/Scripts/python.exe -m pip install numpy tokenizers datasets huggingface-hub tqdm gguf

bash tools/fetch_llamacpp.sh              # pinned llama.cpp build, not committed

.venv/Scripts/python.exe scripts/fetch_data.py --docs 20000
.venv/Scripts/python.exe scripts/train_tokenizer.py --vocab-size 8192
.venv/Scripts/python.exe scripts/tokenize_corpus.py
.venv/Scripts/python.exe scripts/train.py --max-steps 2000
.venv/Scripts/python.exe scripts/export_gguf.py
.venv/Scripts/python.exe scripts/verify_gguf.py          # must print PASS

./tools/llamacpp/llama-quantize.exe data/gguf/pagouro-m1-f32.gguf data/gguf/pagouro-m1-q8_0.gguf Q8_0
./tools/llamacpp/llama-cli.exe -m data/gguf/pagouro-m1-q8_0.gguf -p "What is a hermit crab?" -st -n 40
```

`scripts/train.py --resume` continues from the latest checkpoint. Progress is written to
`runs/train_log.jsonl` as it happens.

**Benchmark on an idle machine.** Mining on this box made training measure 30x slow and looked
exactly like a broken toolchain. See `ENVIRONMENT.md`, Finding 6.

## Layout

```
pagouro/model.py        the transformer
scripts/fetch_data.py   corpus download + ledger row (refuses unlicensed sources)
scripts/train_tokenizer.py
scripts/tokenize_corpus.py
scripts/train.py        training, checkpoint, resume, loss log
scripts/export_gguf.py  GGUF writer (own code; the converter upstream moves between releases)
scripts/verify_gguf.py  proves llama.cpp agrees with PyTorch
corpus.json             the provenance ledger
```

`data/`, `checkpoints/`, `runs/` and `tools/llamacpp/` are generated and not committed.

## Licence

Not yet chosen for the weights; see `docs/DECISIONS.md` O-11, which is a real question because
share-alike sources are a large part of the planned corpus. Code will be Apache 2.0.

---

*Hermit crab: carries a home it can leave. Ouroboros: needs nothing from outside. Both are the
product.*

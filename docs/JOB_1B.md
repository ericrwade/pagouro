# The 1B run — plan, prerequisites, launch shape

**Status: PLAN, not launched.** Requires Eric's explicit "launch" (D-54) and the prerequisites
below. Numbers here are from measured runs (D-55, the Flash run) and are updated as runs land.

## Model (D-6, D-7, D-33)
| | value | note |
|---|---|---|
| params | ~1.03B | dim 2048, 20 layers, 16 heads, 4 kv heads, ffn 6144, vocab 32,768, tied embeddings |
| context | 8,192 (O-12 proposal) | trained at 4k for the stable phase, extended to 8k in the decay phase |
| schedule | WSD (D-48) | warmup 2k steps, stable at 3e-4, last 10% linear decay on the domain-heavy mix |
| tokens | 100B (D-6) | ~100 tokens/parameter |
| batch | 1M tokens/step | e.g. 8 GPUs × 16 × 4096 × accum 2 |
| precision | bf16 autocast | as measured on the A40 |

## Data (D-8, D-9, D-10, D-34)
Built on existing open corpora with ledger rows, tokenized on a CPU pod with `tokenize_corpus.py
--workers 32` (measured 3.4x on 4 workers; ~1 hour per 10B tokens at 8 workers), written to a
**network volume** (~200 GB of uint16 for 100B tokens; volume 500 GB, STANDARD tier, ~$35/month):

| slice | share | source | licence |
|---|---|---|---|
| educational web | ~55% | FineWeb-Edu | ODC-By 1.0 |
| code | ~15% | The Stack (py, rust, go, solidity, c++) | permissive subset |
| encyclopedic | ~12% | Wikipedia (EN) | CC BY-SA 3.0 |
| Q&A | ~8% | Stack Exchange | CC BY-SA |
| canon + government | ~10% | Gutenberg canon (D-38), US gov works | public domain |

The decay phase (last 10B tokens) shifts to a domain-heavy mix (canon, Stack Exchange economics,
bitcointalk voice, crypto synthetic) per D-9. Every row gets its `corpus.json` entry before
training starts; nothing pre-2022-claimed is mixed with synthetic (D-34).

## Cost, from measurement
MFU measured: 15% at 59M, 20% at 126M on the A40 (plain PyTorch, SDPA, bf16). Expect 25–35% at
1B on H100s. 6·N·D = 6 × 1.03e9 × 1e11 = 6.2e20 FLOP.

| MFU | H100-hours | secure $3.49 | community $2.69 | wall clock on 8×H100 |
|---|---|---|---|---|
| 25% | 700 | $2,440 | $1,880 | ~3.6 days |
| 35% | 500 | $1,740 | $1,340 | ~2.6 days |

Plus the data volume, a CPU pod for tokenization (~$5), and one 2-GPU dress rehearsal (~$5).
**Budget line: $1,500–2,500.** The brief's $850 assumed 35% MFU and no overhead.

## Prerequisites (in order)
1. **Flash run finished and evaluated** (D-56): the first model with real knowledge; its
   answered-real and bluff rates tell us whether the recipe works before spending 100x more.
2. **Multi-GPU training.** DONE 2026-09-18: `train.py` runs under torchrun (env-driven DDP, per-rank sampling, one all-reduce per step with grad accumulation, rank-0 checkpoints of the unwrapped module). Rehearsed on a 2×L4 pod ($0.98/h, ~12 min): 60,400 tok/s aggregate, checkpoint + resume proven (`runs/runpod/ddp_rehearsal_2xL4.jsonl`). Gotcha: torchrun swallows `--log`; use `--log-path`. Without multi-GPU, one H100 at 25% MFU is ~29 days: too long
   and too fragile. Needed: DDP (torch.distributed, one process per GPU, data on each GPU,
   gradient all-reduce), tested on a 2×A40 pod for an hour (~$1). Checkpoints stay rank-0-only
   and uncompiled (D-55's `raw_model`).
3. **SFT set in the thousands** with the harness classes (running; 700/class target).
4. **O-12 decided** (8k) and the context-extension step in the decay phase implemented
   (`--seq-len` change on resume with RoPE unchanged: the model has to be told the new max).
5. **Streaming/parallel tokenizer** ✔ (2026-09-18) and the data volume built and ledgered — **with a pre-2022 basis on every backbone row first** (O-22, `docs/O22_PRE2022_BACKBONE.md`; D-34 is locked).
6. Eric's "launch" on the status issue, with the balance loaded.

## Launch shape (what the session will do, step by step, when told)
1. `create-network-volume` 500 GB in a data center with 8×H100 secure stock.
2. CPU pod (or the training pod before the run): fetch + tokenize the mixture to the volume;
   `corpus.json` rows written and committed.
3. `create-pod` 8×H100 SXM secure, image `runpod/pytorch`, volume at `/workspace`, `startSsh`.
4. `make_bundle.sh --no-data` → scp → `on_pod_setup.sh` → `torchrun --nproc_per_node 8
   scripts/train.py --bf16 --data-on-gpu --schedule wsd ...` detached; every 500 steps a checkpoint
   on the volume; the session copies the latest checkpoint home every 6 hours and posts progress.
5. Decay phase on the domain mix with 8k context; then anneal-stage SFT on the pod (minutes).
   The decay data is `build_mixture.py --anneal-only` output: the canon + **the shelf (D-58)**,
   36 licensed works / 10.4M tokens as of 2026-09-18, each capped (`--shelf-cap-chars`) and the
   shelf as a whole ≤ `--shelf-fraction` of the anneal (measured 30% at the defaults). At 1B
   scale the anneal is ~10B tokens, so the shelf is repeated; keep each work under ~4 epochs by
   raising the cap only if the Flash ablation (shelf vs no-shelf, `scripts/runpod/flash_ablation.sh`
   + `scripts/score_heldout.py`) showed the shelf helped on the shared held-out sets. If it did
   not, ship the canon-only anneal and say so on the box.
6. Export, quantize, fidelity check, evals, package; **delete the pod**; keep the volume until the
   checkpoint is verified home, then delete it too.

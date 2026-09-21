# The 1B run — plan, prerequisites, launch shape

**Status: PLAN, not launched.** Requires Eric's explicit "launch" (D-54) and the prerequisites
below. Numbers here are from measured runs (D-55, the Flash run) and are updated as runs land.

## Model (D-6, D-7, D-33)
| | value | note |
|---|---|---|
| params | ~1.03B | dim 2048, 20 layers, 16 heads, 4 kv heads, ffn 6144, vocab 32,768, tied embeddings |
| context | 8,192 (O-12 proposal) | trained at 4k for the stable phase, extended to 8k in the decay phase |
| schedule | WSD (D-48, D-61) | warmup 2k steps, stable at 3e-4, last 10% linear decay on a **mix**: backbone data + domain anneal, with no domain token replayed more than ~2x (the Flash run's anneal-only decay memorised an 8M-token anneal in 1,200 steps: train 3.05->0.48, held-out 3.25->4.82) |
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
| code | ~15% | dated repositories (py, rust, go, solidity, c++) at their last pre-2022 commit (D-62b) | MIT/BSD/Apache/ISC/PSF/CC0 per repo, on the row |
| encyclopedic | ~12% | Wikipedia (EN) | CC BY-SA 3.0 |
| Q&A | ~8% | Stack Exchange | CC BY-SA |
| canon + government | ~10% | Gutenberg canon (D-38), US gov works | public domain |

The decay phase (last 10B tokens) shifts to a domain-heavy mix (canon, the shelf, Stack Exchange economics,
crypto synthetic — bitcointalk EXCLUDED per D-60) per D-9 — **heavy, not exclusive**: the domain
slices are ~10.4M tokens (shelf) + ~7.9M (canon) today, so at 10B decay tokens they can be at most a
few percent of the decay without being replayed dozens of times; the rest of the decay stays backbone
data, and the held-out anneal loss is watched every 250 steps and must not rise (D-61). Every row gets its `corpus.json` entry before
training starts; nothing pre-2022-claimed is mixed with synthetic (D-34).

## Cost, from measurement
MFU measured: 15% at 59M, 20% at 126M on the A40 (plain PyTorch, SDPA, bf16). **Head-to-head with
nanochat's loop on the same A40 (2026-09-19, D-69): nanochat depth-8 (~45M params) 85.6k tok/s =
16.9% MFU by its own meter; ours at 126M 39.0k tok/s ≈ 20%. No efficiency to borrow at this size;
the card, not the loop, is the limit.** Expect 25–35% at 1B on H100s. 6·N·D = 6 × 1.03e9 × 1e11 = 6.2e20 FLOP.

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
5. **Streaming/parallel tokenizer** ✔ (2026-09-18) and the data volume built and ledgered — **with a pre-2022 basis on every backbone row first** (O-22, `docs/O22_PRE2022_BACKBONE.md`; D-34 is locked) — FineWeb and Wikipedia done 2026-09-19; **The Stack replaced by a dated code source ≤ 2021-12-31 (D-62b) ✔ 2026-09-21** — 95 repos, 240.7M tokens, five `code-dated-*` rows. The backbone is fully dated.
6. Eric's "launch" on the status issue, with the balance loaded.

## Staged for the 1B as of 2026-09-20 (what the weekend built; every item measured on Flash first)
- **Decay must be a mix** (D-61): FineWeb + anneal, never anneal-only; the naive decay ate itself at
  126M. `flash.sh` phase 2 is the template; the shelf stays (won every clean held-out set).
- **Yardsticks:** the 100-item honesty sets (`evals/bluff100.json`, `calibration100.json`, D-73)
  adjudicate; the 30-item sets are history. Tool-result fidelity (`evals/toolresult.json`, D-70),
  memory with the numbers column, spelling (novel words, D-68), tool-use with `--probs` (O-35),
  skills on the model (`scripts/skill_test.py --model`). One command: `scripts/eval_sft_ckpt.sh`.
- **SFT mix, ready:** the 5,558 harness set + calc + memory seeds, skill router/answer examples
  (48), spelling seed (501), tool-result seed (600, half failures). At 126M the tool-result rows
  cost 10–16 points of open-question honesty however padded (D-76); the 1B is where that trade
  is expected to relax — measure it on the 100-sets before shipping any mix.
- **GRPO, ready:** `sft/grpo_curriculum.jsonl` (D-71): known 303 / unknowable 2,846 / invented
  2,956 with `train_grpo.py --balance` and the three-way reward; the frozen scorer is the reward.
  97 prompts were memorised in 240 steps (D-69); this set is 61× larger, one pass each.
- **Router probability** (O-35): read from token logprobs; 0.917 right vs 0.816 wrong at 126M,
  overconfident at the top. Fit a temperature on the GRPO curriculum, test on the 100-sets.
- **Corpus facts that stand:** backbone dated (FineWeb dump-date rows, Wikipedia 2021-12-20); the
  Stack replaced by dated repositories (D-62b, 2026-09-21); six shelf manuals re-OCR'd from page images with the
  page-order check on every ingest (D-66); bitcointalk and The Law excluded.
- **Not part of the 1B run but sharing the card:** the drawing model (D-67) — `train_draw.py` at
  5.5M params trains on the desk; a 20–50M version wants an hour of GPU; the Belle Époque LoRA
  (D-75) is a separate, finished artifact.

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

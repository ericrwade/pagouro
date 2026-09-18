#!/usr/bin/env bash
# Master pipeline: corpus -> tokenize -> pretrain -> anneal -> SFT -> export ->
# quantize -> verify -> eval -> package -> copy to USB. Runs unattended.
#
# 2026-09-16 incident: the first real run OOM'd during pretrain at seq_len=1024/
# batch=12 (activation memory for 14 layers of full attention + a 32768-vocab
# logits tensor peaked past 13GB and the OS killed the orchestrator). Because
# this script had no `set -e`, every downstream stage then ran anyway against
# missing files and silently produced a broken "complete" package that got
# copied over the USB drive. Fixed on both fronts: seq_len/batch reduced to a
# config measured stable in isolation (scripts diagnostic, ~2.6GB RSS flat over
# 120 steps vs 13GB+ and climbing at the old config), and explicit fail-fast
# checks added after every stage that produces a file later stages depend on.
set -e
set -x
cd "/c/Users/Eric Wade/PAGOURO_BUILD"
PY=./.venv/Scripts/python.exe
USB="/d"
require() { [ -e "$1" ] || { echo "FATAL: expected file missing: $1" >&2; exit 1; }; }

# START_STAGE=N (default 0) skips every stage numbered below N. Added 2026-09-17
# after stage 7 halted on a harness bug (verify_gguf.py missing -no-cnv) with a
# finished pretrain+anneal on disk and no way to rerun from SFT without
# retraining everything. Stages the run skips must already have left their
# outputs in place; the require checks at each stage boundary still apply.
START_STAGE="${START_STAGE:-0}"
THREADS="${THREADS:-0}"   # torch threads for stages 4-5; 0 = torch default
stage() { if [ "$1" -ge "$START_STAGE" ]; then return 0; else echo "### STAGE $1 SKIPPED (START_STAGE=$START_STAGE) ###"; return 1; fi; }

# SKIP_CORPUS=1 skips stages 0-3 -- set this on a relaunch after stages 0-3
# already completed and produced verified tokenized_real/tokenized_anneal
# directories (re-running build_mixture.py would regenerate pretrain.txt from
# fresh random sampling without retokenizing it here, silently desyncing it
# from the already-tokenized data/tokenized_real/ this run would then train on).
if [ -z "${SKIP_CORPUS:-}" ]; then
  # No pgrep on this system. Poll log files for each script's own completion
  # marker instead of checking process existence -- more portable, and it
  # matches how every other long job in this project reports it is done.
  echo "### STAGE 0: wait for bitcointalk crawl to finish ###"
  until grep -q "ledger updated" /tmp/bct_crawl.log 2>/dev/null; do
    sleep 30
  done
  echo "bitcointalk crawl finished"

  echo "### STAGE 1: rebuild mixture with final anneal data (bitcointalk + crypto) ###"
  $PY -u scripts/build_mixture.py --pretrain-chars 1200000000

  echo "### STAGE 2: wait for pretrain tokenization if still running ###"
  until grep -q "tokenized in" /tmp/tokenize_pretrain.log 2>/dev/null; do
    sleep 15
  done

  echo "### STAGE 3: tokenize the anneal mixture with the same tokenizer ###"
  $PY -u scripts/tokenize_corpus.py --input data/mixture/anneal.txt \
      --tokenizer data/tokenizer_real/tokenizer.json --out data/tokenized_anneal --val-fraction 0.01
else
  echo "### STAGES 0-3 SKIPPED (SKIP_CORPUS=1): reusing existing tokenized_real / tokenized_anneal ###"
  require data/tokenized_real/meta.json
  require data/tokenized_anneal/meta.json
fi

if stage 4; then
echo "### STAGE 4: PRETRAIN (the long pole) ###"
# seq_len=512/batch=8 (was 1024/12): measured flat ~2.6GB RSS over 120 steps,
# vs 13GB+ and still climbing at the old config. Token throughput measured
# ~890-900 tok/s either way (this model's cost is not attention-dominated at
# this size), so the step count below is scaled up to cover the same total
# token budget the original 3000-step plan did (~36.9M tokens), not scaled
# down for speed.
#
# THREADS: torch threads for train.py (default 0 = torch's own default, 16 on
# this box). The 2026-09-17 hard freeze hit at step ~6140 after 8 hours at
# full load on all cores, cause unknown; THREADS=12 leaves thermal headroom.
#
# RESUME_PRETRAIN=1: continue from the existing checkpoints/real_pretrain.pt
# instead of wiping it. Without this flag stage 4 DELETES the checkpoint and
# starts from step 0 -- after the freeze that would have thrown away 6,000
# steps (~7 hours). The run log is trimmed to entries at or before the
# checkpoint step so the resumed steps do not appear twice.
if [ -n "${RESUME_PRETRAIN:-}" ]; then
  echo "### RESUMING pretrain from existing checkpoint (RESUME_PRETRAIN=1) ###"
  require checkpoints/real_pretrain.pt
  $PY - <<'PYEOF'
import json, torch
step = torch.load("checkpoints/real_pretrain.pt", map_location="cpu", weights_only=False)["step"]
rows = [l for l in open("runs/real_pretrain.jsonl", encoding="utf-8") if json.loads(l)["step"] <= step]
open("runs/real_pretrain.jsonl", "w", encoding="utf-8", newline="\n").writelines(rows)
print(f"checkpoint step {step}; run log trimmed to {len(rows)} rows")
PYEOF
  RESUME_FLAG="--resume"
else
  rm -f checkpoints/real_pretrain.pt runs/real_pretrain.jsonl
  RESUME_FLAG=""
fi
$PY -u scripts/train.py $RESUME_FLAG --threads "$THREADS" \
    --dim 512 --layers 14 --heads 8 --kv-heads 2 --seq-len 512 --batch-size 8 \
    --max-steps 9000 --warmup 450 --lr 3e-4 --min-lr 3e-5 \
    --eval-every 300 --ckpt-every 300 --seed 1337 \
    --data-dir data/tokenized_real --ckpt checkpoints/real_pretrain.pt --log runs/real_pretrain.jsonl
require checkpoints/real_pretrain.pt
fi

if stage 5; then
echo "### STAGE 5: ANNEAL (final ~10% of training, domain-heavy) ###"
cp checkpoints/real_pretrain.pt checkpoints/real_anneal.pt
$PY -u scripts/train.py --threads "$THREADS" \
    --dim 512 --layers 14 --heads 8 --kv-heads 2 --seq-len 512 --batch-size 8 \
    --max-steps 10050 --resume --warmup 450 --lr 3e-4 --min-lr 3e-5 \
    --eval-every 150 --ckpt-every 150 --seed 1337 \
    --data-dir data/tokenized_anneal --ckpt checkpoints/real_anneal.pt --log runs/real_anneal.jsonl
require checkpoints/real_anneal.pt
fi

if stage 6; then
echo "### STAGE 6: SFT (loss on response tokens only) ###"
$PY -u scripts/train_sft.py --threads "$THREADS" --checkpoint checkpoints/real_anneal.pt \
    --tokenizer data/tokenizer_real/tokenizer.json --out checkpoints/real_sft.pt \
    --steps 1200 --batch-size 4 --lr 2e-5
require checkpoints/real_sft.pt
fi

if stage 7; then
echo "### STAGE 7: export to GGUF, quantize, verify fidelity ###"
mkdir -p data/gguf_real
$PY -u scripts/export_gguf.py --checkpoint checkpoints/real_sft.pt \
    --tokenizer data/tokenizer_real/tokenizer.json --out data/gguf_real/pagouro-real-f32.gguf \
    --name Pagouro
require data/gguf_real/pagouro-real-f32.gguf
$PY -u scripts/verify_gguf.py --checkpoint checkpoints/real_sft.pt \
    --tokenizer data/tokenizer_real/tokenizer.json --gguf data/gguf_real/pagouro-real-f32.gguf \
    --prompt "The purpose of a constitution is" --tokens 32 > runs/verify_gguf_real.log 2>&1
cat runs/verify_gguf_real.log

./tools/llamacpp/llama-quantize.exe data/gguf_real/pagouro-real-f32.gguf \
    data/gguf_real/pagouro-real-q4_k_m.gguf Q4_K_M
./tools/llamacpp/llama-quantize.exe data/gguf_real/pagouro-real-f32.gguf \
    data/gguf_real/pagouro-real-q8_0.gguf Q8_0
require data/gguf_real/pagouro-real-q4_k_m.gguf
require data/gguf_real/pagouro-real-q8_0.gguf
fi

if stage 8; then
echo "### STAGE 8: real evaluation on the frozen suite ###"
$PY -u evals/run_eval.py --model data/gguf_real/pagouro-real-q8_0.gguf --label pagouro-real \
    --tokens 140 --timeout 90 > runs/pagouro_real_eval.log 2>&1
tail -20 runs/pagouro_real_eval.log
fi

if stage 9; then
echo "### STAGE 9: offline audit ###"
$PY -u evals/offline_audit.py --exe tools/llamacpp/llama-completion.exe \
    --args "-m data/gguf_real/pagouro-real-q8_0.gguf -p hello -n 24 --temp 0 -ngl 0 --no-warmup" \
    --max-seconds 60 --out evals/results/offline_audit_real.json
fi

if stage 10; then
echo "### STAGE 10: assemble the release package ###"
REL="release/Pagouro"
rm -rf "$REL"
mkdir -p "$REL/model" "$REL/docs"
cp data/gguf_real/pagouro-real-q4_k_m.gguf "$REL/model/pagouro-q4_k_m.gguf"
cp data/gguf_real/pagouro-real-q8_0.gguf "$REL/model/pagouro-q8_0.gguf"
cp tools/llamacpp/llama-cli.exe "$REL/"
cp tools/llamacpp/*.dll "$REL/" 2>/dev/null || true
cp corpus.json "$REL/docs/"
cp docs/THREAT_MODEL.md "$REL/docs/" 2>/dev/null || true
cp evals/BASELINES.md "$REL/docs/" 2>/dev/null || true
cp evals/results/pagouro-real__*.json "$REL/docs/" 2>/dev/null || true
cp evals/results/offline_audit_real.json "$REL/docs/" 2>/dev/null || true
mkdir -p "$REL/licenses"
cp licenses/*.txt "$REL/licenses/" 2>/dev/null || true

require "$REL/model/pagouro-q4_k_m.gguf"
require "$REL/model/pagouro-q8_0.gguf"
$PY -u scripts/package_release.py --release-dir "$REL"
fi

if stage 11; then
echo "### STAGE 11: copy to USB ###"
if [ -d "$USB" ]; then
  rm -rf "$USB/Pagouro"
  cp -r "$REL" "$USB/Pagouro"
  echo "copied to USB at $USB/Pagouro"
else
  echo "USB drive $USB not found at copy time -- package left at $REL"
fi
fi

echo "### PIPELINE COMPLETE ###"
date

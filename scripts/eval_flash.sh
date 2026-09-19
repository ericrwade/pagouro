#!/bin/bash
# After FLASH_DONE: turn a fetched Flash checkpoint into numbers, locally, in one go (D-61).
#   bash scripts/eval_flash.sh checkpoints/runpod_flash.pt flash            # base model: raw evals
#   bash scripts/eval_flash.sh checkpoints/runpod_flash.pt flash --sft      # + CPU SFT, then the full suite
#
# Base (no SFT) models get the bluff/calibration/deflection sets in --raw completion mode; the
# tool-use axis needs the router SFT, so it only runs on the SFT'd model. Every output lands in
# data/gguf_<label>/ and evals/results/<label>*__*.json. Numbers, not adjectives.
set -e
cd "$(dirname "$0")/.."
CKPT="${1:?checkpoint}"; LABEL="${2:?label}"; DO_SFT="${3:-}"
PY=./.venv/Scripts/python.exe
TOK=data/tokenizer_real/tokenizer.json
THREADS="${THREADS:-8}"          # D-52: share the machine
SFT_STEPS="${SFT_STEPS:-3000}"
OUT=data/gguf_$LABEL; mkdir -p "$OUT" runs

echo "### 1. checkpoint loads, all finite"
$PY -c "
import torch,sys;ck=torch.load('$CKPT',map_location='cpu',weights_only=False)
ok=all(torch.isfinite(v).all().item() for v in ck['model'].values() if v.is_floating_point())
print('step',ck['step'],'tensors',len(ck['model']),'finite',ok,'config',ck['config']); sys.exit(0 if ok and len(ck['model'])>=129 else 1)"

echo "### 2. export base -> GGUF f32, quantize q8_0, verify fidelity (-no-cnv)"
$PY -u scripts/export_gguf.py --checkpoint "$CKPT" --tokenizer $TOK --out "$OUT/pagouro-$LABEL-f32.gguf" --name "Pagouro-$LABEL"
./tools/llamacpp/llama-quantize.exe "$OUT/pagouro-$LABEL-f32.gguf" "$OUT/pagouro-$LABEL-q8_0.gguf" q8_0 > /dev/null
$PY -u scripts/verify_gguf.py --checkpoint "$CKPT" --tokenizer $TOK --gguf "$OUT/pagouro-$LABEL-f32.gguf" \
    --prompt "The purpose of a constitution is" --tokens 32 | tail -3

echo "### 3. base-model evals (raw completion mode; tool-use needs SFT)"
$PY -u evals/run_eval.py --model "$OUT/pagouro-$LABEL-q8_0.gguf" --label "$LABEL-base" --raw --tokens 140 --timeout 120 > "runs/eval_$LABEL-base.log" 2>&1
tail -8 "runs/eval_$LABEL-base.log"

if [ "$DO_SFT" = "--sft" ]; then
  echo "### 4. CPU SFT from the base (THREADS=$THREADS, $SFT_STEPS steps) -- check machine load first"
  $PY -u scripts/train_sft.py --threads "$THREADS" --checkpoint "$CKPT" --tokenizer $TOK \
      --out "checkpoints/${LABEL}_sft.pt" --steps "$SFT_STEPS" --batch-size 4 --lr 2e-5 --log "runs/sft_$LABEL.jsonl" 2>&1 | tail -5
  echo "### 5. export SFT -> GGUF, quantize, verify"
  $PY -u scripts/export_gguf.py --checkpoint "checkpoints/${LABEL}_sft.pt" --tokenizer $TOK --out "$OUT/pagouro-$LABEL-sft-f32.gguf" --name "Pagouro-$LABEL-sft"
  ./tools/llamacpp/llama-quantize.exe "$OUT/pagouro-$LABEL-sft-f32.gguf" "$OUT/pagouro-$LABEL-sft-q8_0.gguf" q8_0 > /dev/null
  $PY -u scripts/verify_gguf.py --checkpoint "checkpoints/${LABEL}_sft.pt" --tokenizer $TOK --gguf "$OUT/pagouro-$LABEL-sft-f32.gguf" \
      --prompt "The purpose of a constitution is" --tokens 32 | tail -3
  echo "### 6. full suite on the SFT'd model"
  $PY -u evals/run_eval.py --model "$OUT/pagouro-$LABEL-sft-q8_0.gguf" --label "$LABEL" --tokens 140 --timeout 120 > "runs/eval_$LABEL.log" 2>&1
  tail -8 "runs/eval_$LABEL.log"
  $PY -u evals/run_tooluse.py --model "$OUT/pagouro-$LABEL-sft-q8_0.gguf" --label "$LABEL" > "runs/tooluse_$LABEL.log" 2>&1
  tail -4 "runs/tooluse_$LABEL.log"
fi
echo "EVAL_FLASH_DONE $LABEL"

#!/usr/bin/env bash
# Evaluate one SFT checkpoint end to end: export -> quantise -> verify -> the frozen suite, tool-use
# with router probabilities (O-35), memory (with the numbers column), spelling (D-68), and the
# skills test on the model (O-30). Numbers, not adjectives.
#
#   bash scripts/eval_sft_ckpt.sh checkpoints/flash_sft3.pt flash-sft3 pagouro-flash3
#   args: <checkpoint> <gguf stem label> <eval label>
set -euo pipefail
cd "$(dirname "$0")/.."
CKPT="$1"; STEM="$2"; LABEL="$3"
PY=./.venv/Scripts/python.exe
TOK=data/tokenizer_real/tokenizer.json
THREADS="${THREADS:-8}"
OUT=data/gguf_flash; mkdir -p "$OUT" runs
echo "### export $CKPT -> $OUT/pagouro-$STEM-{f32,q8_0}.gguf"
$PY -u scripts/export_gguf.py --checkpoint "$CKPT" --tokenizer $TOK --out "$OUT/pagouro-$STEM-f32.gguf" --name "Pagouro-$STEM"
./tools/llamacpp/llama-quantize.exe "$OUT/pagouro-$STEM-f32.gguf" "$OUT/pagouro-$STEM-q8_0.gguf" q8_0 > /dev/null
$PY -u scripts/verify_gguf.py --checkpoint "$CKPT" --tokenizer $TOK --gguf "$OUT/pagouro-$STEM-f32.gguf" \
    --prompt "The purpose of a constitution is" --tokens 32 | tail -3
M="$OUT/pagouro-$STEM-q8_0.gguf"
echo "### frozen suite"
$PY -u evals/run_eval.py --model "$M" --label "$LABEL" --tokens 140 --timeout 120 > "runs/eval_$LABEL.log" 2>&1; tail -6 "runs/eval_$LABEL.log"
echo "### tool-use with probabilities"
$PY -u evals/run_tooluse.py --model "$M" --label "$LABEL" --threads "$THREADS" --probs > "runs/tooluse_$LABEL.log" 2>&1; tail -3 "runs/tooluse_$LABEL.log"
echo "### memory"
$PY -u evals/run_memory.py --model "$M" --label "$LABEL" --threads "$THREADS" > "runs/memory_$LABEL.log" 2>&1; tail -1 "runs/memory_$LABEL.log"
echo "### spelling"
$PY -u evals/run_spelling.py --model "$M" --label "$LABEL" --threads "$THREADS" > "runs/spelling_$LABEL.log" 2>&1; tail -1 "runs/spelling_$LABEL.log"
echo "### skills on the model"
$PY -u scripts/skill_test.py --all --model "$M" --threads "$THREADS" > "runs/skills_$LABEL.log" 2>&1; grep -E "^(date_math|recipe_scale|unit_convert):" "runs/skills_$LABEL.log"
echo "EVAL_SFT_DONE $LABEL"

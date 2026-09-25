#!/usr/bin/env bash
# Evaluate a model that arrives as an f32 GGUF (the 1B exports from the pod, D-85): quantise to q8_0
# and q4_k_m, then the same measurements as eval_sft_ckpt.sh (the frozen suite, the 100-sets, tool-use
# with probabilities, memory, spelling, tool-result fidelity, skills). Numbers, not adjectives.
#
#   bash scripts/eval_gguf.sh checkpoints/pagouro-1b/pagouro-1b-sftA-f32.gguf 1b-sftA pagouro-1b-sftA
#   args: <f32 gguf> <gguf stem label> <eval label>     (THREADS=8 default; the 1B on CPU is ~8x slower than Flash)
set -euo pipefail
cd "$(dirname "$0")/.."
F32="$1"; STEM="$2"; LABEL="$3"
PY=./.venv/Scripts/python.exe
THREADS="${THREADS:-8}"
OUT=data/gguf_1b; mkdir -p "$OUT" runs
echo "### quantise $F32 -> $OUT/pagouro-$STEM-{q8_0,q4_k_m}.gguf"
./tools/llamacpp/llama-quantize.exe "$F32" "$OUT/pagouro-$STEM-q8_0.gguf" q8_0 > /dev/null
./tools/llamacpp/llama-quantize.exe "$F32" "$OUT/pagouro-$STEM-q4_k_m.gguf" q4_k_m > /dev/null
ls -la "$OUT/pagouro-$STEM-q8_0.gguf" "$OUT/pagouro-$STEM-q4_k_m.gguf" | awk '{print $5, $9}'
M="$OUT/pagouro-$STEM-q8_0.gguf"
echo "### frozen suite"
# D-91: FREE answers (the honesty sets, deflection) decode with the app's repetition penalty; the copying suites below do not.
REPEAT_PENALTY="${FREE_PENALTY:-1.0}" $PY -u evals/run_eval.py --model "$M" --label "$LABEL" --tokens 140 --timeout 120 > "runs/eval_$LABEL.log" 2>&1; tail -6 "runs/eval_$LABEL.log"
echo "### 100-item honesty sets (D-73: the adjudicating numbers)"
REPEAT_PENALTY="${FREE_PENALTY:-1.0}" $PY -u evals/run_eval.py --model "$M" --label "$LABEL" --set all100 --tokens 140 --timeout 120 > "runs/eval100_$LABEL.log" 2>&1; grep -E "^  -> " "runs/eval100_$LABEL.log"
echo "### tool-use with probabilities"
$PY -u evals/run_tooluse.py --model "$M" --label "$LABEL" --threads "$THREADS" --probs > "runs/tooluse_$LABEL.log" 2>&1; tail -3 "runs/tooluse_$LABEL.log"
echo "### memory"
$PY -u evals/run_memory.py --model "$M" --label "$LABEL" --threads "$THREADS" > "runs/memory_$LABEL.log" 2>&1; tail -1 "runs/memory_$LABEL.log"
echo "### spelling"
$PY -u evals/run_spelling.py --model "$M" --label "$LABEL" --threads "$THREADS" > "runs/spelling_$LABEL.log" 2>&1; tail -1 "runs/spelling_$LABEL.log"
echo "### tool-result fidelity (D-70)"
$PY -u evals/run_toolresult.py --model "$M" --label "$LABEL" --threads "$THREADS" > "runs/toolresult_$LABEL.log" 2>&1; tail -1 "runs/toolresult_$LABEL.log"
echo "### skills on the model"
$PY -u scripts/skill_test.py --all --model "$M" --threads "$THREADS" > "runs/skills_$LABEL.log" 2>&1; grep -E "^(date_math|recipe_scale|unit_convert):" "runs/skills_$LABEL.log"
echo "EVAL_GGUF_DONE $LABEL"

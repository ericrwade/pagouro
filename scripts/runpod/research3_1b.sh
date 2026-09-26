#!/usr/bin/env bash
# Runs ON A ONE-GPU POD (D-95 → round 3, Eric: "round 3 and if you need to, round 4"): the whole lineage that
# produced GRPO-3 (SFT → GRPO on the D-71 curriculum → 70 % soup → GRPO on the self-knowledge curriculum),
# started from SFT-v3, the fine-tune that already holds the program-traced reasoning seed (reasoning held-out
# 18 → 93 of 320). The reasoning kind rides in BOTH curricula (balanced by kind) so the RL rounds do not erode it.
#   needs at /workspace: pagouro-1b-sft3.pt (from round 2), the code bundle (sft/, app/, evals/, scripts/soup.py)
#   bash scripts/runpod/research3_1b.sh
# Outputs: /workspace/out/{pagouro-1b-grpoA.pt, pagouro-1b-soupA.pt, pagouro-1b-grpoB.pt, logs, SHA256SUMS}.
# GGUF export happens on the desk (export_gguf.py from the .pt), to keep the pod's clock for training.
set -e
cd /workspace/pagouro
mkdir -p /workspace/out runs
SFT=/workspace/pagouro-1b-sft3.pt
TOK=data/tokenizer_real/tokenizer.json
cat sft/grpo_curriculum.jsonl sft/grpo_reasoning.jsonl > sft/grpo_curA.jsonl        # D-71 kinds + reasoning
cat sft/grpo_selfknow.jsonl  sft/grpo_reasoning.jsonl > sft/grpo_curB.jsonl        # self-knowledge kinds + reasoning
echo "== $(date -u +%H:%MZ) GRPO-A from sft3 on the D-71 curriculum + reasoning, ${A_STEPS:-100} steps, ${MAX_NEW:-128}-token samples =="
python -u scripts/train_grpo.py --checkpoint "$SFT" --tokenizer "$TOK" --out /workspace/out/pagouro-1b-grpoA.pt \
    --set sft/grpo_curA.jsonl --balance --steps "${A_STEPS:-100}" --prompts-per-step 8 --group 8 --max-new "${MAX_NEW:-128}" --lr 2e-6 --kl 0.05 \
    --save-every 25 --log /workspace/out/grpoA_log.jsonl 2>&1 | grep --line-buffered -E "^GRPO|^step +[0-9]*[05] |saved|written|Error|Traceback" | tail -30
echo "== $(date -u +%H:%MZ) soup: ${SOUP_ALPHA:-0.7} GRPO-A + $(python -c "print(round(1-${SOUP_ALPHA:-0.7},2))") sft3 =="
python -u scripts/soup.py --a "$SFT" --b /workspace/out/pagouro-1b-grpoA.pt --alpha "${SOUP_ALPHA:-0.7}" --out /workspace/out/pagouro-1b-soupA.pt 2>&1 | tail -1
echo "== $(date -u +%H:%MZ) GRPO-B from the soup on self-knowledge + reasoning, ${B_STEPS:-50} steps =="
python -u scripts/train_grpo.py --checkpoint /workspace/out/pagouro-1b-soupA.pt --tokenizer "$TOK" --out /workspace/out/pagouro-1b-grpoB.pt \
    --set sft/grpo_curB.jsonl --balance --steps "${B_STEPS:-50}" --prompts-per-step 8 --group 8 --max-new "${MAX_NEW:-128}" --lr 2e-6 --kl 0.05 \
    --save-every 25 --log /workspace/out/grpoB_log.jsonl 2>&1 | grep --line-buffered -E "^GRPO|^step +[0-9]*[05] |saved|written|Error|Traceback" | tail -20
cd /workspace/out && rm -f SHA256SUMS && sha256sum * > SHA256SUMS && ls -la
echo "$(date -u +%H:%MZ) RESEARCH3_1B_DONE"

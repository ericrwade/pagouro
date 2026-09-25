#!/usr/bin/env bash
# Runs ON A ONE-GPU POD (D-92 research plan, items 1-2): a fresh SFT from the pretrained base with the two
# new seeds in the mix -- the argue seed (reason under a premise, O-45 #3) and the self-knowledge
# abstentions (abstain where this model was measured not to know, O-45 #1) -- then GRPO on the
# self-knowledge curriculum from that SFT, exports, hashes. Soups and evals happen on the desk.
#   needs at /workspace: pagouro-1b-base-model.pt (model-only checkpoint), the code bundle, sft/, skills/
#   bash scripts/runpod/research_1b.sh
set -e
cd /workspace/pagouro
mkdir -p /workspace/out runs
BASE=/workspace/pagouro-1b-base-model.pt
TOK=data/tokenizer_real/tokenizer.json
echo "== $(date -u +%H:%MZ) SFT v2 from the base: mix B + argue_seed x${ARGUE_REPEAT:-20} + selfknow abstentions x${SELFKNOW_REPEAT:-1} =="
python -u scripts/train_sft.py --checkpoint "$BASE" --tokenizer "$TOK" --out /workspace/out/pagouro-1b-sft2.pt \
    --steps "${SFT_STEPS:-3000}" --batch-size 4 --lr 1e-5 --repeat argue_seed.jsonl="${ARGUE_REPEAT:-20}" selfknow_abstain_seed.jsonl="${SELFKNOW_REPEAT:-1}" \
    --log /workspace/out/sft2.jsonl 2>&1 | grep --line-buffered -E "examples|step +[0-9]*00 |written|Error|Traceback" | tail -8
python -u scripts/export_gguf.py --checkpoint /workspace/out/pagouro-1b-sft2.pt --tokenizer "$TOK" --out /workspace/out/pagouro-1b-sft2-f32.gguf --name Pagouro-1B-sft2 2>&1 | tail -1
echo "== $(date -u +%H:%MZ) GRPO-4 from sft2 on the self-knowledge curriculum, ${GRPO_STEPS:-75} steps =="
python -u scripts/train_grpo.py --checkpoint /workspace/out/pagouro-1b-sft2.pt --tokenizer "$TOK" --out /workspace/out/pagouro-1b-grpo4.pt \
    --set sft/grpo_selfknow.jsonl --balance --steps "${GRPO_STEPS:-75}" --prompts-per-step 8 --group 8 --max-new 64 --lr 2e-6 --kl 0.05 \
    --save-every 25 --log /workspace/out/grpo4_log.jsonl 2>&1 | grep --line-buffered -E "^GRPO|^step +[0-9]*[05] |saved|written|Error|Traceback" | tail -20
python -u scripts/export_gguf.py --checkpoint /workspace/out/pagouro-1b-grpo4.pt --tokenizer "$TOK" --out /workspace/out/pagouro-1b-grpo4-f32.gguf --name Pagouro-1B-grpo4 2>&1 | tail -1
cd /workspace/out && rm -f SHA256SUMS && sha256sum * > SHA256SUMS && ls -la
echo "$(date -u +%H:%MZ) RESEARCH_1B_DONE"

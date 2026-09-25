#!/usr/bin/env bash
# Runs ON A ONE-GPU POD (D-93 research plan, round 2): a fresh SFT from the pretrained base with the
# recipe the first round taught us -- argue seed x20 BEFORE any GRPO, the multi-turn seed, the
# self-knowledge abstentions at a fifth of their weight (x1 made SFT-v2 over-abstain: 37/70), and the
# new program-traced reasoning seed (O-45 #3; the 1B solved 7/200 word problems before it) -- then GRPO
# on the merged curriculum (self-knowledge + reasoning, balanced by kind, 160-token samples so a trace
# can finish), exports, hashes. Evals happen on the desk (frozen suite + multi-turn + reasoning held-out).
#   needs at /workspace: pagouro-1b-base-model.pt (model-only checkpoint), the code bundle (sft/, app/, evals/, skills/)
#   bash scripts/runpod/research2_1b.sh
set -e
cd /workspace/pagouro
mkdir -p /workspace/out runs
BASE=/workspace/pagouro-1b-base-model.pt
TOK=data/tokenizer_real/tokenizer.json
cat sft/grpo_selfknow.jsonl sft/grpo_reasoning.jsonl > sft/grpo_mix2.jsonl
echo "== $(date -u +%H:%MZ) SFT v3 from the base: mix B + argue x${ARGUE_REPEAT:-20} + multiturn + selfknow x${SELFKNOW_REPEAT:-0.2} + reasoning x${REASON_REPEAT:-0.5} =="
python -u scripts/train_sft.py --checkpoint "$BASE" --tokenizer "$TOK" --out /workspace/out/pagouro-1b-sft3.pt \
    --steps "${SFT_STEPS:-3000}" --batch-size 4 --lr 1e-5 \
    --repeat argue_seed.jsonl="${ARGUE_REPEAT:-20}" selfknow_abstain_seed.jsonl="${SELFKNOW_REPEAT:-0.2}" reasoning_seed_gen.jsonl="${REASON_REPEAT:-0.5}" \
    --log /workspace/out/sft3.jsonl 2>&1 | grep --line-buffered -E "examples|step +[0-9]*00 |written|Error|Traceback" | tail -8
python -u scripts/export_gguf.py --checkpoint /workspace/out/pagouro-1b-sft3.pt --tokenizer "$TOK" --out /workspace/out/pagouro-1b-sft3-f32.gguf --name Pagouro-1B-sft3 2>&1 | tail -1
echo "== $(date -u +%H:%MZ) GRPO-5 from sft3 on self-knowledge + reasoning, ${GRPO_STEPS:-75} steps, 160-token samples =="
python -u scripts/train_grpo.py --checkpoint /workspace/out/pagouro-1b-sft3.pt --tokenizer "$TOK" --out /workspace/out/pagouro-1b-grpo5.pt \
    --set sft/grpo_mix2.jsonl --balance --steps "${GRPO_STEPS:-75}" --prompts-per-step 8 --group 8 --max-new 160 --lr 2e-6 --kl 0.05 \
    --save-every 25 --log /workspace/out/grpo5_log.jsonl 2>&1 | grep --line-buffered -E "^GRPO|^step +[0-9]*[05] |saved|written|Error|Traceback" | tail -20
python -u scripts/export_gguf.py --checkpoint /workspace/out/pagouro-1b-grpo5.pt --tokenizer "$TOK" --out /workspace/out/pagouro-1b-grpo5-f32.gguf --name Pagouro-1B-grpo5 2>&1 | tail -1
cd /workspace/out && rm -f SHA256SUMS && sha256sum * > SHA256SUMS && ls -la
echo "$(date -u +%H:%MZ) RESEARCH2_1B_DONE"

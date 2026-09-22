#!/usr/bin/env bash
# Runs ON THE TRAINING POD after train_1b.sh prints PAGOURO_1B_DONE: SFT on one GPU, export to GGUF,
# and leave everything under /workspace/out for the session to copy home (quantise + evals happen on
# the desk with tools/llamacpp, D-76: two SFT mixes are measured on the 100-sets before one ships).
#   bash scripts/runpod/finish_1b.sh            # needs sft/ and skills/ copied to /workspace/pagouro first
set -e
cd /workspace/pagouro
mkdir -p /workspace/out
CK=/workspace/ckpt/pagouro-1b.pt
TOK=data/tokenizer_real/tokenizer.json
STEPS="${STEPS:-3000}"; LR="${LR:-1e-5}"; BS="${BS:-4}"
echo "== export the pretrained model first (the base is an artefact of its own) =="
python -u scripts/export_gguf.py --checkpoint "$CK" --tokenizer "$TOK" --out /workspace/out/pagouro-1b-base-f32.gguf --name Pagouro-1B-base 2>&1 | tail -2
echo "== SFT A: the shipped mix (sft3 recipe: every seed EXCEPT the tool-result seed), $STEPS steps, lr $LR =="
python -u scripts/train_sft.py --checkpoint "$CK" --tokenizer "$TOK" --out /workspace/out/pagouro-1b-sftA.pt \
    --steps "$STEPS" --batch-size "$BS" --lr "$LR" --repeat toolresult_seed.jsonl=0 --log /workspace/out/sftA.jsonl 2>&1 | grep --line-buffered -E "examples|step +[0-9]*00 |written|Error" | tail -20
echo "== SFT B: A + the tool-result seed (D-70/D-76: the trade the 1B is expected to relax) =="
python -u scripts/train_sft.py --checkpoint "$CK" --tokenizer "$TOK" --out /workspace/out/pagouro-1b-sftB.pt \
    --steps "$STEPS" --batch-size "$BS" --lr "$LR" --log /workspace/out/sftB.jsonl 2>&1 | grep --line-buffered -E "examples|step +[0-9]*00 |written|Error" | tail -20
for v in A B; do
  python -u scripts/export_gguf.py --checkpoint /workspace/out/pagouro-1b-sft$v.pt --tokenizer "$TOK" --out /workspace/out/pagouro-1b-sft$v-f32.gguf --name Pagouro-1B 2>&1 | tail -1
done
cp /workspace/train.log /workspace/runs/pagouro-1b.jsonl /workspace/out/ 2>/dev/null || true
ls -la /workspace/out/
echo FINISH_1B_DONE

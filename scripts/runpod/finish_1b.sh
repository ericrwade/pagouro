#!/usr/bin/env bash
# Runs ON THE TRAINING POD after train_1b.sh prints PAGOURO_1B_DONE: SFT on two GPUs in parallel (mix A
# on GPU 0, mix B on GPU 1 -- the pod bills for eight cards whether one or two work), export to GGUF,
# and leave everything under /workspace/out for the session to copy home (quantise + evals happen on
# the desk with tools/llamacpp, D-76: two SFT mixes are measured on the 100-sets before one ships).
#   bash scripts/runpod/finish_1b.sh            # needs sft/ and skills/ copied to /workspace/pagouro first
set -e
cd /workspace/pagouro
mkdir -p /workspace/out
CK=/workspace/ckpt/pagouro-1b.pt
TOK=data/tokenizer_real/tokenizer.json
STEPS="${STEPS:-3000}"; LR="${LR:-1e-5}"; BS="${BS:-4}"
FILT='examples|step +[0-9]*00 |written|Error|Traceback'
echo "== $(date -u +%H:%MZ) export the pretrained model first (the base is an artefact of its own) =="
python -u scripts/export_gguf.py --checkpoint "$CK" --tokenizer "$TOK" --out /workspace/out/pagouro-1b-base-f32.gguf --name Pagouro-1B-base 2>&1 | tail -2
echo "== $(date -u +%H:%MZ) SFT A (GPU 0): the shipped mix (sft3 recipe: every seed EXCEPT the tool-result seed), $STEPS steps, lr $LR =="
echo "== SFT B (GPU 1): A + the tool-result seed (D-70/D-76: the trade the 1B is expected to relax) =="
CUDA_VISIBLE_DEVICES=0 python -u scripts/train_sft.py --checkpoint "$CK" --tokenizer "$TOK" --out /workspace/out/pagouro-1b-sftA.pt \
    --steps "$STEPS" --batch-size "$BS" --lr "$LR" --repeat toolresult_seed.jsonl=0 --log /workspace/out/sftA.jsonl > /workspace/out/sftA.stdout 2>&1 &
PA=$!
CUDA_VISIBLE_DEVICES=1 python -u scripts/train_sft.py --checkpoint "$CK" --tokenizer "$TOK" --out /workspace/out/pagouro-1b-sftB.pt \
    --steps "$STEPS" --batch-size "$BS" --lr "$LR" --log /workspace/out/sftB.jsonl > /workspace/out/sftB.stdout 2>&1 &
PB=$!
wait $PA; RA=$?; wait $PB; RB=$?
echo "== $(date -u +%H:%MZ) SFT A exit $RA / SFT B exit $RB =="
grep -E "$FILT" /workspace/out/sftA.stdout | tail -6
grep -E "$FILT" /workspace/out/sftB.stdout | tail -6
[ "$RA" -eq 0 ] && [ "$RB" -eq 0 ] || { echo "FINISH_1B_SFT_FAILED"; exit 1; }
for v in A B; do
  python -u scripts/export_gguf.py --checkpoint /workspace/out/pagouro-1b-sft$v.pt --tokenizer "$TOK" --out /workspace/out/pagouro-1b-sft$v-f32.gguf --name Pagouro-1B 2>&1 | tail -1
done
cp /workspace/train.log /workspace/runs/pagouro-1b.jsonl /workspace/runs/pagouro-1b.stdout /workspace/out/ 2>/dev/null || true
cp /workspace/volume/decay_mix/meta.json /workspace/out/decay_mix.meta.json 2>/dev/null || true
ls -la /workspace/out/
echo "$(date -u +%H:%MZ) FINISH_1B_DONE"

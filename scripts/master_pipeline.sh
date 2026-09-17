#!/usr/bin/env bash
# Master pipeline: corpus -> tokenize -> pretrain -> anneal -> SFT -> export ->
# quantize -> verify -> eval -> package -> copy to USB. Runs unattended.
set -x
cd "/c/Users/Eric Wade/PAGOURO_BUILD"
PY=./.venv/Scripts/python.exe
USB="/d"

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

echo "### STAGE 4: PRETRAIN (the long pole) ###"
rm -f checkpoints/real_pretrain.pt runs/real_pretrain.jsonl
$PY -u scripts/train.py \
    --dim 512 --layers 14 --heads 8 --kv-heads 2 --seq-len 1024 --batch-size 12 \
    --max-steps 3000 --warmup 150 --lr 3e-4 --min-lr 3e-5 \
    --eval-every 200 --ckpt-every 200 --seed 1337 \
    --data-dir data/tokenized_real --ckpt checkpoints/real_pretrain.pt --log runs/real_pretrain.jsonl

echo "### STAGE 5: ANNEAL (final ~10% of training, domain-heavy) ###"
cp checkpoints/real_pretrain.pt checkpoints/real_anneal.pt
$PY -u scripts/train.py \
    --dim 512 --layers 14 --heads 8 --kv-heads 2 --seq-len 1024 --batch-size 12 \
    --max-steps 3350 --resume --warmup 150 --lr 3e-4 --min-lr 3e-5 \
    --eval-every 50 --ckpt-every 50 --seed 1337 \
    --data-dir data/tokenized_anneal --ckpt checkpoints/real_anneal.pt --log runs/real_anneal.jsonl

echo "### STAGE 6: SFT (loss on response tokens only) ###"
$PY -u scripts/train_sft.py --checkpoint checkpoints/real_anneal.pt \
    --tokenizer data/tokenizer_real/tokenizer.json --out checkpoints/real_sft.pt \
    --steps 1200 --batch-size 4 --lr 2e-5

echo "### STAGE 7: export to GGUF, quantize, verify fidelity ###"
mkdir -p data/gguf_real
$PY -u scripts/export_gguf.py --checkpoint checkpoints/real_sft.pt \
    --tokenizer data/tokenizer_real/tokenizer.json --out data/gguf_real/pagouro-real-f32.gguf \
    --name Pagouro
$PY -u scripts/verify_gguf.py --checkpoint checkpoints/real_sft.pt \
    --tokenizer data/tokenizer_real/tokenizer.json --gguf data/gguf_real/pagouro-real-f32.gguf \
    --prompt "The purpose of a constitution is" --tokens 32 > runs/verify_gguf_real.log 2>&1
cat runs/verify_gguf_real.log

./tools/llamacpp/llama-quantize.exe data/gguf_real/pagouro-real-f32.gguf \
    data/gguf_real/pagouro-real-q4_k_m.gguf Q4_K_M
./tools/llamacpp/llama-quantize.exe data/gguf_real/pagouro-real-f32.gguf \
    data/gguf_real/pagouro-real-q8_0.gguf Q8_0

echo "### STAGE 8: real evaluation on the frozen suite ###"
$PY -u evals/run_eval.py --model data/gguf_real/pagouro-real-q8_0.gguf --label pagouro-real \
    --tokens 140 --timeout 90 > runs/pagouro_real_eval.log 2>&1
tail -20 runs/pagouro_real_eval.log

echo "### STAGE 9: offline audit ###"
$PY -u evals/offline_audit.py --exe tools/llamacpp/llama-completion.exe \
    --args "-m data/gguf_real/pagouro-real-q8_0.gguf -p hello -n 24 --temp 0 -ngl 0 --no-warmup" \
    --max-seconds 60 --out evals/results/offline_audit_real.json

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

$PY -u scripts/package_release.py --release-dir "$REL"

echo "### STAGE 11: copy to USB ###"
if [ -d "$USB" ]; then
  rm -rf "$USB/Pagouro"
  cp -r "$REL" "$USB/Pagouro"
  echo "copied to USB at $USB/Pagouro"
else
  echo "USB drive $USB not found at copy time -- package left at $REL"
fi

echo "### PIPELINE COMPLETE ###"
date

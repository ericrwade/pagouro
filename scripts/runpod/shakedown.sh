#!/usr/bin/env bash
# Runs ON THE POD. The pipeline shakedown on a rented GPU (D-54): the real 59M
# config, bf16, data on the GPU, 300 steps with a checkpoint, then a resume for
# 60 more steps to prove resume on this hardware. Prints tokens/second, which is
# the number that prices the 1B run. Everything lands under /workspace/runs.
set -e
cd /workspace/pagouro
mkdir -p /workspace/runs /workspace/ckpt
STEPS="${STEPS:-300}"
python -u scripts/train.py --bf16 --data-on-gpu \
    --dim 512 --layers 14 --heads 8 --kv-heads 2 --seq-len 512 --batch-size 32 \
    --max-steps "$STEPS" --warmup 30 --lr 3e-4 --min-lr 3e-5 \
    --eval-every 150 --ckpt-every 150 --seed 1337 \
    --data-dir data/tokenized_real --ckpt /workspace/ckpt/shakedown.pt --log /workspace/runs/shakedown.jsonl \
    2>&1 | tee /workspace/runs/shakedown.stdout | grep -E "device|parameters|tokens/step|step +[0-9]+ \||val loss|checkpoint|done in"
echo "== resume proof (D-22) =="
python -u scripts/train.py --bf16 --data-on-gpu --resume \
    --dim 512 --layers 14 --heads 8 --kv-heads 2 --seq-len 512 --batch-size 32 \
    --max-steps $((STEPS + 60)) --warmup 30 --lr 3e-4 --min-lr 3e-5 \
    --eval-every 150 --ckpt-every 150 --seed 1337 \
    --data-dir data/tokenized_real --ckpt /workspace/ckpt/shakedown.pt --log /workspace/runs/shakedown.jsonl \
    2>&1 | tee -a /workspace/runs/shakedown.stdout | grep -E "RESUMED|step +[0-9]+ \||done in"
python - <<'EOF'
import json
rows=[json.loads(l) for l in open('/workspace/runs/shakedown.jsonl')]
tr=[r for r in rows if 'tokens_per_s' in r]
print("SUMMARY tokens/s (last 5 logged):", [r['tokens_per_s'] for r in tr[-5:]])
print("SUMMARY best val:", min((r['val_loss'] for r in rows if 'val_loss' in r), default=None))
EOF

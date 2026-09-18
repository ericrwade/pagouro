#!/usr/bin/env bash
# Runs ON THE POD (2+ GPUs). Proves multi-GPU training end to end before the 1B run
# (docs/JOB_1B.md prerequisite 2): torchrun with one process per GPU, the 59M config,
# 100 steps, a checkpoint, then a resume for 40 more steps. Prints tokens/s so the
# per-GPU efficiency can be compared with the single-GPU number.
set -e
cd /workspace/pagouro
mkdir -p /workspace/runs /workspace/ckpt
N=$(nvidia-smi -L | wc -l)
echo "== $N GPUs =="
nvidia-smi -L
COMMON="--bf16 --data-on-gpu --dim 512 --layers 14 --heads 8 --kv-heads 2 --seq-len 512 --batch-size 16 \
  --warmup 10 --lr 3e-4 --min-lr 3e-5 --eval-every 50 --ckpt-every 50 --seed 1337 \
  --data-dir data/tokenized_real --ckpt /workspace/ckpt/ddp.pt --log-path /workspace/runs/ddp.jsonl"
torchrun --nproc_per_node "$N" scripts/train.py $COMMON --max-steps 100 2>&1 | tee /workspace/runs/ddp.stdout \
  | grep --line-buffered -E "DDP|device|tokens/step|step +[0-9]+ \||val loss|checkpoint|done in|Error|error"
echo "== resume proof (D-22, multi-GPU) =="
torchrun --nproc_per_node "$N" scripts/train.py $COMMON --max-steps 140 --resume 2>&1 | tee -a /workspace/runs/ddp.stdout \
  | grep --line-buffered -E "RESUMED|step +[0-9]+ \||done in|Error|error"
python - <<'EOF'
import json
rows=[json.loads(l) for l in open('/workspace/runs/ddp.jsonl')]
tr=[r for r in rows if 'tokens_per_s' in r and r['step']>=40]
print("SUMMARY tokens/s (steps >= 40):", round(sum(r['tokens_per_s'] for r in tr)/max(1,len(tr))))
EOF
echo DDP_DONE

#!/bin/bash
# D-65 / O-24: nanochat's training loop vs ours on the same GPU, ten minutes, ~$0.10.
# Measures tokens/s and MFU of nanochat's base_train at a ~Flash-sized model (depth 8 -> dim 512,
# 2048 context, their tokenizer/data), then our train.py at the Flash config (dim 768 x 16 layers,
# 1024 context) for 100 steps on our data. Different tokenizers and shapes, so this is a LOOP
# efficiency comparison (MFU), not a model comparison. Both numbers go into docs/JOB_1B.md.
#
#   bash scripts/runpod/nanochat_headtohead.sh     # on the pod, after on_pod_setup.sh
set -e
cd /workspace
export OMP_NUM_THREADS=1
export NANOCHAT_BASE_DIR=/workspace/nanochat_cache
mkdir -p $NANOCHAT_BASE_DIR
[ -d nanochat ] || git clone --depth 1 https://github.com/karpathy/nanochat.git
cd nanochat
command -v uv &> /dev/null || (curl -LsSf https://astral.sh/uv/install.sh | sh; export PATH="$HOME/.local/bin:$PATH")
export PATH="$HOME/.local/bin:$PATH"
[ -d .venv ] || uv venv
uv sync --extra gpu 2>&1 | tail -2
source .venv/bin/activate
python -m nanochat.dataset -n 4 2>&1 | tail -1          # a few shards is enough for 150 steps
python -m scripts.tok_train 2>&1 | tail -1
echo "== nanochat base_train: depth 8, 150 steps, device batch 16 =="
torchrun --standalone --nproc_per_node=1 -m scripts.base_train -- --depth=8 --num-iterations=150 --device-batch-size=16 \
    --eval-every=-1 --run=dummy 2>&1 | tee /workspace/runs/nanochat_h2h.log | grep -E "step 000(5|9|14)|tok/sec|mfu|MFU|Number of parameters|params" | tail -8
deactivate
cd /workspace/pagouro
echo "== ours: train.py, Flash config, 100 steps, bf16, data on GPU =="
python -u scripts/train.py --bf16 --data-on-gpu --dim 768 --layers 16 --heads 12 --kv-heads 4 --seq-len 1024 \
  --batch-size 16 --grad-accum 4 --max-steps 100 --warmup 10 --lr 6e-4 --eval-every 1000 --ckpt-every 1000 --seed 1 \
  --ckpt /workspace/ckpt/h2h_ours.pt --log /workspace/runs/h2h_ours.jsonl --data-dir /workspace/data/flash \
  2>&1 | tee /workspace/runs/ours_h2h.log | grep -E "parameters|step +(50|90|99) \|" | tail -4
echo H2H_DONE

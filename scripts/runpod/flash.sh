#!/usr/bin/env bash
# Runs ON THE POD. "Pagouro Flash": the ~150M Baby tier (D-50), trained on a few
# billion tokens of FineWeb-Edu fetched by the pod itself (fast link, same ledger
# row as the local slice: ODC-By 1.0), tokenized with our tokenizer, checkpointed
# to /workspace (mount a network volume there). Resumable: rerun the same command.
#
#   DOCS=1500000 TOKENS_TARGET=3000000000 bash scripts/runpod/flash.sh
set -e
cd /workspace/pagouro
mkdir -p /workspace/runs /workspace/ckpt /workspace/data
DOCS="${DOCS:-1500000}"                 # FineWeb-Edu documents to stream (~1k tokens each; 1.5M -> ~1.5B tokens)
STEPS="${STEPS:-0}"                     # 0 = derive from TOKENS_TARGET
TOKENS_TARGET="${TOKENS_TARGET:-3000000000}"
BATCH="${BATCH:-64}"; SEQ="${SEQ:-1024}"
COMPILE="${COMPILE:-}"                    # set COMPILE=--compile to measure the torch.compile arm
if [ ! -f /workspace/data/flash/meta.json ]; then
  echo "== fetch + tokenize (once) =="
  [ -f /workspace/data/fineweb-edu-flash.txt ] || \
    python -u scripts/fetch_data.py --dataset HuggingFaceFW/fineweb-edu --config sample-10BT \
        --docs "$DOCS" --out /workspace/data/fineweb-edu-flash.txt
  python -u scripts/tokenize_corpus.py --input /workspace/data/fineweb-edu-flash.txt \
      --tokenizer data/tokenizer_real/tokenizer.json --out /workspace/data/flash --val-fraction 0.002
fi
if [ "$STEPS" = "0" ]; then STEPS=$(( TOKENS_TARGET / (BATCH * SEQ) )); fi
echo "== train: ~150M params, $STEPS steps x $((BATCH * SEQ)) tokens =="
RESUME=""; [ -f /workspace/ckpt/flash.pt ] && RESUME="--resume"
python -u scripts/train.py --bf16 --data-on-gpu $COMPILE $RESUME \
    --dim 768 --layers 16 --heads 12 --kv-heads 4 --seq-len "$SEQ" --batch-size "$BATCH" \
    --max-steps "$STEPS" --warmup 500 --lr 6e-4 --min-lr 6e-5 \
    --eval-every 500 --ckpt-every 500 --seed 1337 \
    --data-dir /workspace/data/flash --ckpt /workspace/ckpt/flash.pt --log /workspace/runs/flash.jsonl \
    2>&1 | tee -a /workspace/runs/flash.stdout | grep -E "RESUMED|device|parameters|tokens/step|step +[0-9]*00 \||val loss|checkpoint|done in"

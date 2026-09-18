#!/usr/bin/env bash
# Runs ON THE POD. "Pagouro Flash": the ~150M Baby tier (D-50), trained with the
# real recipe (D-9, D-48): warmup-stable-decay, the stable phase on FineWeb-Edu the
# pod fetches itself (ODC-By 1.0, same ledger row as the local slice), the DECAY
# phase (the anneal) on the domain-heavy mix shipped in the bundle. Checkpoints to
# /workspace. Resumable: rerun the same command and it continues from the checkpoint.
#
#   DOCS=1500000 TOKENS_TARGET=2000000000 bash scripts/runpod/flash.sh
set -e
cd /workspace/pagouro
mkdir -p /workspace/runs /workspace/ckpt /workspace/data
DOCS="${DOCS:-1500000}"                 # FineWeb-Edu documents to stream (~1k tokens each; 1.5M -> ~1.6B tokens)
TOKENS_TARGET="${TOKENS_TARGET:-2000000000}"
BATCH="${BATCH:-64}"; SEQ="${SEQ:-1024}"
STABLE="${STABLE:-0.9}"                 # fraction of steps at full lr; the rest is the anneal on domain data
COMPILE="${COMPILE:-}"                    # set COMPILE=--compile to use torch.compile (measure first)
if [ ! -f /workspace/data/flash/meta.json ]; then
  echo "== fetch + tokenize (once) =="
  [ -f /workspace/data/fineweb-edu-flash.txt ] || \
    python -u scripts/fetch_data.py --dataset HuggingFaceFW/fineweb-edu --config sample-10BT \
        --docs "$DOCS" --out /workspace/data/fineweb-edu-flash.txt
  python -u scripts/tokenize_corpus.py --input /workspace/data/fineweb-edu-flash.txt \
      --tokenizer data/tokenizer_real/tokenizer.json --out /workspace/data/flash --val-fraction 0.002
fi
STEPS=$(( TOKENS_TARGET / (BATCH * SEQ) ))
DECAY_START=$(python -c "print(int($STEPS * $STABLE))")
COMMON="--bf16 --data-on-gpu $COMPILE --dim 768 --layers 16 --heads 12 --kv-heads 4 --seq-len $SEQ --batch-size $BATCH \
  --max-steps $STEPS --schedule wsd --stable-until $STABLE --warmup 500 --lr 6e-4 --min-lr 6e-5 \
  --eval-every 500 --ckpt-every 500 --seed 1337 --ckpt /workspace/ckpt/flash.pt --log /workspace/runs/flash.jsonl"
FILTER='RESUMED|device|parameters|tokens/step|torch.compile|step +[0-9]*00 \||val loss|checkpoint|done in'
CUR=$(python -c "import torch,os;print(torch.load('/workspace/ckpt/flash.pt',map_location='cpu',weights_only=False)['step']+1 if os.path.exists('/workspace/ckpt/flash.pt') else 0)")
echo "== flash: ~150M params, $STEPS steps x $((BATCH * SEQ)) tokens; stable until step $DECAY_START; resuming at $CUR =="
if [ "$CUR" -lt "$DECAY_START" ]; then
  echo "== phase 1: stable lr on FineWeb-Edu =="
  RESUME=""; [ "$CUR" -gt 0 ] && RESUME="--resume"
  python -u scripts/train.py $COMMON $RESUME --data-dir /workspace/data/flash --stop-at "$DECAY_START" \
      2>&1 | tee -a /workspace/runs/flash.stdout | grep --line-buffered -E "$FILTER"
fi
echo "== phase 2: decay (anneal) on the domain mix =="
python -u scripts/train.py $COMMON --resume --data-dir data/tokenized_anneal \
    2>&1 | tee -a /workspace/runs/flash.stdout | grep --line-buffered -E "$FILTER"
echo FLASH_DONE

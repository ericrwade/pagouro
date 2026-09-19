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
BATCH="${BATCH:-16}"; ACCUM="${ACCUM:-4}"; SEQ="${SEQ:-1024}"   # 16 x 1024 x 4 = 65k tokens/step; batch 64 OOMs a 44 GB A40
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
STEPS=$(( TOKENS_TARGET / (BATCH * SEQ * ACCUM) ))
DECAY_START=$(python -c "print(int($STEPS * $STABLE))")
COMMON="--bf16 --data-on-gpu $COMPILE --dim 768 --layers 16 --heads 12 --kv-heads 4 --seq-len $SEQ --batch-size $BATCH --grad-accum $ACCUM \
  --max-steps $STEPS --schedule wsd --stable-until $STABLE --warmup 500 --lr 6e-4 --min-lr 6e-5 \
  --eval-every 500 --ckpt-every 500 --seed 1337 --ckpt /workspace/ckpt/flash.pt --log /workspace/runs/flash.jsonl"
FILTER='RESUMED|device|parameters|tokens/step|torch.compile|step +[0-9]*00 \||val loss|checkpoint|done in'
CUR=$(python -c "import torch,os;print(torch.load('/workspace/ckpt/flash.pt',map_location='cpu',weights_only=False)['step']+1 if os.path.exists('/workspace/ckpt/flash.pt') else 0)")
echo "== flash: ~126M params, $STEPS steps x $((BATCH * SEQ * ACCUM)) tokens; stable until step $DECAY_START; resuming at $CUR =="
if [ "$CUR" -lt "$DECAY_START" ]; then
  echo "== phase 1: stable lr on FineWeb-Edu =="
  RESUME=""; [ "$CUR" -gt 0 ] && RESUME="--resume"
  python -u scripts/train.py $COMMON $RESUME --data-dir /workspace/data/flash --stop-at "$DECAY_START" \
      2>&1 | tee -a /workspace/runs/flash.stdout | grep --line-buffered -E "$FILTER"
fi
# D-61 (2026-09-19): the decay must be a MIX. Anneal-only decay replayed an 8M-token anneal ~25x
# over the 200M-token phase and memorised it (train 3.05->0.48, held-out anneal 3.25->4.82).
# Phase 2 data = FW_DECAY_TOKENS of the FineWeb stream + the anneal, so domain tokens are seen
# ~1-2x. ANNEAL_DIR selects canon-only (default) or the shelf build.
ANNEAL_DIR="${ANNEAL_DIR:-data/tokenized_anneal}"
FW_DECAY_TOKENS="${FW_DECAY_TOKENS:-150000000}"
DECAY_DIR=data/decay_mix_$(basename "$ANNEAL_DIR")
if [ ! -f "$DECAY_DIR/meta.json" ]; then
  python - "$ANNEAL_DIR" "$DECAY_DIR" "$FW_DECAY_TOKENS" <<'PY'
import json, os, sys, numpy as np
src, out, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
os.makedirs(out, exist_ok=True)
fw = np.memmap('/workspace/data/flash/train.bin', dtype=np.uint16, mode='r')
off = int(np.random.default_rng(1337).integers(0, len(fw) - N))
dom = np.fromfile(os.path.join(src, 'train.bin'), dtype=np.uint16)
mix = np.concatenate([np.asarray(fw[off:off + N]), dom]); mix.tofile(os.path.join(out, 'train.bin'))
np.fromfile(os.path.join(src, 'val.bin'), dtype=np.uint16).tofile(os.path.join(out, 'val.bin'))
meta = json.load(open(os.path.join(src, 'meta.json')))
meta.update({'decay_mix': {'fineweb_tokens': N, 'fineweb_offset': off, 'domain_tokens': int(len(dom)),
             'domain_share': round(len(dom) / len(mix), 4), 'source': src}, 'train_tokens': int(len(mix))})
json.dump(meta, open(os.path.join(out, 'meta.json'), 'w'), indent=1)
print(f"decay mix {out}: {len(mix):,} tokens, domain {100*len(dom)/len(mix):.1f}%")
PY
fi
echo "== phase 2: decay on the MIX ($DECAY_DIR); watch the held-out anneal loss, it must not rise =="
python -u scripts/train.py $COMMON --resume --data-dir "$DECAY_DIR" \
    2>&1 | tee -a /workspace/runs/flash.stdout | grep --line-buffered -E "$FILTER"
echo FLASH_DONE

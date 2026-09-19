#!/bin/bash
# D-61 redesign of the Flash decay phase. The naive decay (anneal-only data, ~8M tokens replayed
# ~25x over a 200M-token decay) memorised the anneal: train loss 3.05 -> 0.48 while the held-out
# anneal loss rose 3.25 -> 4.82 in 1,200 steps. Stopped at step ~28,700 (2026-09-19 08:38 UTC).
#
# This version: decay data = a 45M-token FineWeb-Edu slice + the domain anneal (canon, or canon +
# shelf), so no domain token is seen more than ~1.2x; the decay is 1,000 steps (65M tokens) from
# the SAME stable-end checkpoint, same seed, same schedule shape (LR 6e-4 -> 6e-5 linear).
# Two arms for the D-58 ablation:  bash flash_decay_mix.sh canon   |   bash flash_decay_mix.sh shelf
set -e
cd /workspace/pagouro
ARM="${1:?canon|shelf}"
SRC=data/tokenized_anneal; [ "$ARM" = "shelf" ] && SRC=data/tokenized_anneal_shelf
OUT=data/decay_$ARM
if [ ! -f $OUT/meta.json ]; then
  python - "$SRC" "$OUT" <<'PY'
import json, os, sys, numpy as np
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
fw = np.memmap('/workspace/data/flash/train.bin', dtype=np.uint16, mode='r')
rng = np.random.default_rng(1337)
N = 45_000_000
off = int(rng.integers(0, len(fw) - N))
dom = np.fromfile(os.path.join(src, 'train.bin'), dtype=np.uint16)
mix = np.concatenate([np.asarray(fw[off:off + N]), dom])
mix.tofile(os.path.join(out, 'train.bin'))
val = np.fromfile(os.path.join(src, 'val.bin'), dtype=np.uint16); val.tofile(os.path.join(out, 'val.bin'))
meta = json.load(open(os.path.join(src, 'meta.json')))
meta.update({'decay_mix': {'fineweb_tokens': N, 'fineweb_offset': off, 'domain_tokens': int(len(dom)),
             'domain_share': round(len(dom) / len(mix), 4), 'source': src}, 'train_tokens': int(len(mix)), 'val_tokens': int(len(val))})
json.dump(meta, open(os.path.join(out, 'meta.json'), 'w'), indent=1)
print(f"{out}: {len(mix):,} train tokens ({len(dom):,} domain = {100*len(dom)/len(mix):.1f}%), fineweb offset {off:,}")
PY
fi
CK=/workspace/ckpt/flash_mix_$ARM.pt
cp /workspace/ckpt/flash_stable.pt $CK
# max-steps 28464 with stable-until 0.9649 -> decay starts at int(28464*0.9649)=27464, the stable end.
python -u scripts/train.py --bf16 --data-on-gpu --dim 768 --layers 16 --heads 12 --kv-heads 4 --seq-len 1024 \
  --batch-size 16 --grad-accum 4 --max-steps 28464 --schedule wsd --stable-until 0.9649 --warmup 500 \
  --lr 6e-4 --min-lr 6e-5 --eval-every 250 --ckpt-every 250 --seed 1337 --resume \
  --ckpt $CK --log /workspace/runs/flash_mix_$ARM.jsonl --data-dir $OUT \
  2>&1 | tee -a /workspace/runs/flash_mix_$ARM.stdout | grep --line-buffered -E "RESUMED|step +[0-9]*00 \||val loss|checkpoint|done in"
echo "MIX_DONE $ARM"

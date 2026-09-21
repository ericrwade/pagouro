#!/usr/bin/env bash
# Runs ON THE 8-GPU POD (D-82, JOB_1B steps 3-5). Pagouro 1B: dim 2048 / 20 layers / 16 heads / 4 kv,
# ~1B params, WSD schedule, 4k context in the stable phase and 8k in the decay (D-81), the decay a MIX
# (D-61). Data: the volume built by build_volume.py, copied to the pod's LOCAL disk first (random
# window reads from a network filesystem are the wrong shape). Checkpoints and logs go to the network
# volume every CKPT steps; the session copies the latest checkpoint home every 6 h. Resumable: rerun
# the same command and it continues from the checkpoint.
#
#   VOLUME=/workspace/volume bash scripts/runpod/train_1b.sh            # after the volume is mounted/copied
#   Rehearsal (1 hour, D-54 rule): REHEARSAL=1 STEPS_OVERRIDE=300 bash scripts/runpod/train_1b.sh
set -e
cd /workspace/pagouro
VOLUME="${VOLUME:-/workspace/volume}"        # train.bin / val.bin / meta.json from build_volume.py
LOCAL="${LOCAL:-/data1b}"                    # container-local copy (fast random reads); needs ~2x tokens bytes
NGPU="${NGPU:-8}"
BATCH="${BATCH:-8}"; ACCUM="${ACCUM:-4}"; SEQ="${SEQ:-4096}"     # 8 x 4096 x 4 x 8 GPUs = 1,048,576 tokens/step
STABLE="${STABLE:-0.9}"                      # last 10% is the decay on the mix at 8k (D-81)
WARMUP="${WARMUP:-2000}"
LR="${LR:-3e-4}"; MINLR="${MINLR:-3e-5}"
CKPT_EVERY="${CKPT_EVERY:-500}"
COMPILE="${COMPILE:-}"                       # set COMPILE=--compile after the rehearsal measures it
mkdir -p /workspace/runs /workspace/ckpt "$LOCAL"

if [ ! -f "$LOCAL/meta.json" ]; then
  echo "== copying the volume to local disk ($(du -sh "$VOLUME/train.bin" | cut -f1)) =="
  cp "$VOLUME/meta.json" "$LOCAL/"; cp "$VOLUME/val.bin" "$LOCAL/"; cp "$VOLUME/train.bin" "$LOCAL/"
  python - "$LOCAL" <<'PY'
import json, os, sys
d = sys.argv[1]; m = json.load(open(os.path.join(d, "meta.json")))
n = os.path.getsize(os.path.join(d, "train.bin")) // 2
assert n == m["train_tokens"], (n, m["train_tokens"])
print(f"local copy verified: {n:,} train tokens")
PY
fi
TOK_PER_STEP=$(( BATCH * SEQ * ACCUM * NGPU ))
TOTAL_TOKENS=$(python -c "import json;print(json.load(open('$LOCAL/meta.json'))['train_tokens'])")
STEPS=$(( TOTAL_TOKENS / TOK_PER_STEP ))
[ -n "${STEPS_OVERRIDE:-}" ] && STEPS="$STEPS_OVERRIDE"
DECAY_START=$(python -c "print(int($STEPS * $STABLE))")
CKPT=/workspace/ckpt/pagouro-1b.pt
COMMON="--bf16 $COMPILE --dim 2048 --layers 20 --heads 16 --kv-heads 4 --batch-size $BATCH --grad-accum $ACCUM \
  --max-steps $STEPS --schedule wsd --stable-until $STABLE --warmup $WARMUP --lr $LR --min-lr $MINLR \
  --eval-every $CKPT_EVERY --ckpt-every $CKPT_EVERY --seed 1337 --ckpt $CKPT --log-path /workspace/runs/pagouro-1b.jsonl"
FILTER='RESUMED|device|parameters|tokens/step|torch.compile|step +[0-9]*00 \||val loss|checkpoint|done in|Error|error|Traceback'
CUR=$(python -c "import torch,os;print(torch.load('$CKPT',map_location='cpu',weights_only=False)['step']+1 if os.path.exists('$CKPT') else 0)")
echo "== pagouro-1b: $STEPS steps x $TOK_PER_STEP tokens = $(( STEPS * TOK_PER_STEP / 1000000000 ))B; stable until $DECAY_START; resuming at $CUR; $NGPU GPUs =="
if [ "$CUR" -lt "$DECAY_START" ]; then
  echo "== phase 1: stable lr, 4k context, the whole volume =="
  RESUME=""; [ "$CUR" -gt 0 ] && RESUME="--resume"
  torchrun --standalone --nproc_per_node "$NGPU" scripts/train.py $COMMON $RESUME --seq-len "$SEQ" \
      --data-dir "$LOCAL" --stop-at "$DECAY_START" \
      2>&1 | tee -a /workspace/runs/pagouro-1b.stdout | grep --line-buffered -E "$FILTER"
fi
[ -n "${REHEARSAL:-}" ] && { echo "REHEARSAL_DONE"; exit 0; }
# Phase 2 (D-61, D-81): decay on a MIX -- the volume's backbone plus the domain anneal, domain seen ~2x --
# at 8k context: same tokens per step, half the batch, double the accumulation.
ANNEAL_DIR="${ANNEAL_DIR:-data/tokenized_anneal}"
DECAY_DIR="$LOCAL/decay_mix"
DECAY_TOKENS=$(( (STEPS - DECAY_START) * TOK_PER_STEP ))
if [ ! -f "$DECAY_DIR/meta.json" ]; then
  python - "$LOCAL" "$ANNEAL_DIR" "$DECAY_DIR" "$DECAY_TOKENS" <<'PY'
import json, os, sys, numpy as np
local, src, out, N = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
os.makedirs(out, exist_ok=True)
fw = np.memmap(os.path.join(local, 'train.bin'), dtype=np.uint16, mode='r')
dom = np.fromfile(os.path.join(src, 'train.bin'), dtype=np.uint16)
reps = 2                                                  # the domain slice is seen ~2x over the decay (D-61)
n_fw = max(0, N - reps * len(dom))
off = int(np.random.default_rng(1337).integers(0, len(fw) - n_fw))
with open(os.path.join(out, 'train.bin'), 'wb') as f:
    np.asarray(fw[off:off + n_fw]).tofile(f)              # backbone slice (contiguous window of the shuffled-at-build volume)
    for _ in range(reps): dom.tofile(f)
np.fromfile(os.path.join(src, 'val.bin'), dtype=np.uint16).tofile(os.path.join(out, 'val.bin'))   # held-out anneal loss (D-61 gate)
meta = json.load(open(os.path.join(src, 'meta.json')))
meta.update({'decay_mix': {'backbone_tokens': n_fw, 'backbone_offset': off, 'domain_tokens': int(len(dom)), 'domain_reps': reps,
             'domain_share': round(reps * len(dom) / (n_fw + reps * len(dom)), 5), 'source': src}, 'train_tokens': int(n_fw + reps * len(dom))})
json.dump(meta, open(os.path.join(out, 'meta.json'), 'w'), indent=1)
print(f"decay mix {out}: {n_fw + reps*len(dom):,} tokens, domain {100*reps*len(dom)/(n_fw+reps*len(dom)):.2f}%")
PY
fi
echo "== phase 2: decay on the MIX at 8k context; the held-out anneal loss must not rise (D-61) =="
torchrun --standalone --nproc_per_node "$NGPU" scripts/train.py $COMMON --resume --seq-len 8192 \
    --batch-size $(( BATCH / 2 )) --grad-accum $(( ACCUM * 2 )) --data-dir "$DECAY_DIR" \
    2>&1 | tee -a /workspace/runs/pagouro-1b.stdout | grep --line-buffered -E "$FILTER"
echo PAGOURO_1B_DONE

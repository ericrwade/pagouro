# SUPERSEDED 2026-09-19 by flash_decay_mix.sh (D-61): the anneal-only decay memorised the anneal. Kept for the record.
#!/bin/bash
# D-58 guardrail (3): shelf vs no-shelf at Flash scale. Re-runs ONLY the decay phase (the last
# 10% of steps) from the stable-phase-end checkpoint that stable_watch.sh copied to
# /workspace/ckpt/flash_stable.pt, on the shelf anneal (data/tokenized_anneal_shelf) instead of
# the canon-only anneal. Same seed, same schedule, same everything else, so the two final
# models differ only in the anneal data. ~3,050 steps at ~1.7 s = ~1.4 h on an A40 (~$0.70).
#
#   bash scripts/runpod/flash_ablation.sh    # after FLASH_DONE
set -e
cd /workspace/pagouro
[ -f /workspace/ckpt/flash_stable.pt ] || { echo "no flash_stable.pt -- the watcher did not fire"; exit 1; }
[ -f data/tokenized_anneal_shelf/meta.json ] || { echo "no shelf anneal on the pod"; exit 1; }
TOKENS_TARGET="${TOKENS_TARGET:-2000000000}"
BATCH="${BATCH:-16}"; ACCUM="${ACCUM:-4}"; SEQ="${SEQ:-1024}"; STABLE="${STABLE:-0.9}"; COMPILE="${COMPILE:-}"
STEPS=$(( TOKENS_TARGET / (BATCH * SEQ * ACCUM) ))
cp /workspace/ckpt/flash_stable.pt /workspace/ckpt/flash_shelf.pt   # train.py resumes in place; keep the stable copy pristine
COMMON="--bf16 --data-on-gpu $COMPILE --dim 768 --layers 16 --heads 12 --kv-heads 4 --seq-len $SEQ --batch-size $BATCH --grad-accum $ACCUM \
  --max-steps $STEPS --schedule wsd --stable-until $STABLE --warmup 500 --lr 6e-4 --min-lr 6e-5 \
  --eval-every 500 --ckpt-every 500 --seed 1337 --ckpt /workspace/ckpt/flash_shelf.pt --log /workspace/runs/flash_shelf.jsonl"
FILTER='RESUMED|device|parameters|tokens/step|torch.compile|step +[0-9]*00 \||val loss|checkpoint|done in'
CUR=$(python -c "import torch;print(torch.load('/workspace/ckpt/flash_shelf.pt',map_location='cpu',weights_only=False)['step']+1)")
echo "== flash ablation: decay on the SHELF anneal from step $CUR to $STEPS =="
python -u scripts/train.py $COMMON --resume --data-dir data/tokenized_anneal_shelf \
    2>&1 | tee -a /workspace/runs/flash_shelf.stdout | grep --line-buffered -E "$FILTER"
echo ABLATION_DONE

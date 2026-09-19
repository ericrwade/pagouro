#!/bin/bash
# Score both ablation arms (D-58 / D-60) on the SAME held-out tokens. Run on the pod after
# ABLATION_DONE. Sets, and what each one can honestly say:
#   flash/val.bin            FineWeb-only val, held out of both arms         -> general-text cost of the shelf
#   heldout/*.bin            whole works held out of BOTH arms               -> the clean comparison
#                            (communist-manifesto = canon-like; symbolic-logic, neets-13 = shelf-like)
#   tokenized_anneal/val.bin canon-arm val (arm B's train has other canon passages) -> A held-out; B contaminated, reported as such
#   tokenized_anneal_shelf/val.bin  shelf-arm val; arm A never saw the shelf   -> B held-out; A = "no shelf" baseline
set -e
cd /workspace/pagouro
for arm in flash_stable flash_mix_canon flash_mix_shelf flash_naive_decay_partial; do   # D-61: stable end, the two mixed-decay arms, and the stopped naive decay for the record
  python -u scripts/score_heldout.py --ckpt /workspace/ckpt/$arm.pt --seq-len 1024 --batch-size 16 \
    --data /workspace/data/flash/val.bin \
    --data data/heldout/communist-manifesto.bin --data data/heldout/symbolic-logic.bin --data data/heldout/neets-13.bin \
    --data data/tokenized_anneal/val.bin --data data/tokenized_anneal_shelf/val.bin \
    --tokenizer data/tokenizer_real/tokenizer.json \
    --out /workspace/runs/heldout_$arm.json
done
echo SCORED

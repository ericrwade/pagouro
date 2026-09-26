#!/usr/bin/env bash
# Runs ON A ONE-GPU POD (D-95 → round 4, Eric: "and if you need to, round 4"). Two GRPO jobs on the
# curriculum built from each model's OWN failures on the four unanswerable categories the old curriculum
# lacked (sft/build_unanswerable_set.py → scripts/probe_unanswerable.py → sft/grpo_hard_<model>.jsonl):
#   C  from GRPO-B (round 3: reasoning 99/320, bluff 49): hard_grpoB + self-knowledge real/unknowable + reasoning
#   C' from GRPO-3 (the shipped model, bluff 22):          hard_grpo3 + self-knowledge real/unknowable
# Both balanced by kind, 128-token samples, checkpoints every 25 steps.
#   needs at /workspace: pagouro-1b-grpoB.pt, pagouro-1b-grpo3.pt, the code bundle (sft/ incl. grpo_hard_*.jsonl)
#   bash scripts/runpod/research4_1b.sh
set -e
cd /workspace/pagouro
mkdir -p /workspace/out runs
TOK=data/tokenizer_real/tokenizer.json
python - <<'EOF'
import json, io
sk = [json.loads(l) for l in io.open("sft/grpo_selfknow.jsonl", encoding="utf-8") if l.strip()]
sk = [r for r in sk if r["kind"] in ("real", "unknowable_real")]          # the hard set is the only 'invented' kind
rs = [json.loads(l) for l in io.open("sft/grpo_reasoning.jsonl", encoding="utf-8") if l.strip()]
for name, hard, extra in (("grpo_curC.jsonl", "sft/grpo_hard_grpoB.jsonl", rs), ("grpo_curCp.jsonl", "sft/grpo_hard_grpo3.jsonl", [])):
    h = [json.loads(l) for l in io.open(hard, encoding="utf-8") if l.strip()]
    rows = h + sk + extra
    with io.open("sft/" + name, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(name, len(rows), {k: sum(1 for r in rows if r["kind"] == k) for k in ("invented", "real", "unknowable_real", "reasoning")})
EOF
echo "== $(date -u +%H:%MZ) GRPO-C from GRPO-B on its own hard set + self-knowledge + reasoning, ${STEPS:-75} steps =="
python -u scripts/train_grpo.py --checkpoint /workspace/pagouro-1b-grpoB.pt --tokenizer "$TOK" --out /workspace/out/pagouro-1b-grpoC.pt \
    --set sft/grpo_curC.jsonl --balance --steps "${STEPS:-75}" --prompts-per-step 8 --group 8 --max-new 128 --lr 2e-6 --kl 0.05 \
    --save-every 25 --log /workspace/out/grpoC_log.jsonl 2>&1 | grep --line-buffered -E "^GRPO|^step +[0-9]*[05] |saved|written|Error|Traceback" | tail -20
echo "== $(date -u +%H:%MZ) GRPO-C' from GRPO-3 (shipped) on its own hard set + self-knowledge, ${STEPS:-75} steps =="
python -u scripts/train_grpo.py --checkpoint /workspace/pagouro-1b-grpo3.pt --tokenizer "$TOK" --out /workspace/out/pagouro-1b-grpoCp.pt \
    --set sft/grpo_curCp.jsonl --balance --steps "${STEPS:-75}" --prompts-per-step 8 --group 8 --max-new 128 --lr 2e-6 --kl 0.05 \
    --save-every 25 --log /workspace/out/grpoCp_log.jsonl 2>&1 | grep --line-buffered -E "^GRPO|^step +[0-9]*[05] |saved|written|Error|Traceback" | tail -20
cd /workspace/out && rm -f SHA256SUMS && sha256sum * > SHA256SUMS && ls -la
echo "$(date -u +%H:%MZ) RESEARCH4_1B_DONE"

#!/usr/bin/env bash
# Runs ON THE DESK (Git Bash) after finish_1b.sh prints FINISH_1B_DONE on the pod: hash every
# artefact on the pod, copy /workspace/out (GGUF exports, SFT checkpoints, SFT logs, train.log,
# the run jsonl) and the final pretraining checkpoint home, and verify every hash locally.
# The pod is billed until it is deleted, so this is one command and it ends in PASS or FAIL.
#   POD_HOST=63.141.33.76 POD_PORT=22042 KEY=/tmp/rpkey bash scripts/runpod/bring_home_1b.sh
# Rehearsal on small files: POD_OUT=/workspace/out_test POD_CKPT=/workspace/out_test/ck.pt OUT=... CK=...
set -e
POD_HOST="${POD_HOST:?}"; POD_PORT="${POD_PORT:?}"; KEY="${KEY:-/tmp/rpkey}"
POD_OUT="${POD_OUT:-/workspace/out}"; POD_CKPT="${POD_CKPT:-/workspace/ckpt/pagouro-1b.pt}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${OUT:-$ROOT/data/out_1b}"; CK="${CK:-$ROOT/checkpoints/pagouro-1b}"
SSH="ssh -i $KEY -p $POD_PORT -o StrictHostKeyChecking=no root@$POD_HOST"
mkdir -p "$OUT" "$CK"

echo "== hashing on the pod =="
$SSH "cd $POD_OUT && rm -f SHA256SUMS && ls -la && sha256sum * > SHA256SUMS && sha256sum $POD_CKPT | sed 's#  .*#  pagouro-1b-final.pt#' > CKPT.sha && cat SHA256SUMS CKPT.sha"

echo "== copying $POD_OUT -> $OUT =="
scp -i "$KEY" -P "$POD_PORT" -o StrictHostKeyChecking=no "root@$POD_HOST:$POD_OUT/*" "$OUT/"
echo "== copying the final checkpoint -> $CK/pagouro-1b-final.pt =="
scp -i "$KEY" -P "$POD_PORT" -o StrictHostKeyChecking=no "root@$POD_HOST:$POD_CKPT" "$CK/pagouro-1b-final.pt"

echo "== verifying =="
( cd "$OUT" && sha256sum -c SHA256SUMS )
CK_EXPECT=$(cut -c1-64 "$OUT/CKPT.sha")
CK_GOT=$(sha256sum "$CK/pagouro-1b-final.pt" | cut -c1-64)
if [ "$CK_EXPECT" = "$CK_GOT" ]; then echo "pagouro-1b-final.pt: OK"; else echo "pagouro-1b-final.pt: FAILED"; exit 1; fi
ls -la "$OUT" "$CK"
echo "BRING_HOME_1B_PASS -- every file hashed on the pod matches its copy here; safe to delete the pod"

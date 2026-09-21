#!/usr/bin/env bash
# Runs ON THE CPU POD (D-82 step 1): build the 1B data volume onto the network volume at /workspace/volume.
# Resumable: build_volume.py skips finished shards. Log: /workspace/volume/build.log, progress: volume.progress
#   bash scripts/runpod/volume.sh [workers]
set -e
cd /workspace/pagouro
W="${1:-16}"
python -m pip install -q --disable-pip-version-check --break-system-packages numpy tokenizers datasets mwparserfromhell 2>&1 | tail -1
[ -f /workspace/.env ] && set -a && . /workspace/.env && set +a
mkdir -p /workspace/volume data/raw/code
# the dated code (D-62b): re-fetched here on the datacenter link (git), ~40 min; skipped if present
if [ ! -f data/raw/code/cpp.txt ]; then python scripts/fetch_dated_code.py > /workspace/volume/code_fetch.log 2>&1; fi
nohup python -u scripts/build_volume.py --plan plans/volume_1b.json --out /workspace/volume --workers "$W" \
  > /workspace/volume/volume.progress 2>&1 &
echo "volume build started (pid $!), workers $W; tail /workspace/volume/volume.progress"

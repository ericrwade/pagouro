#!/usr/bin/env bash
# Runs ON THE TRAINING POD: fetch one huge file from another pod over N parallel SSH byte-range
# streams (a single stream across datacentres is latency-bound: measured 16 MB/s Iceland -> Montreal).
#   SRC_HOST=... SRC_PORT=... KEY=/root/.ssh/id_ed25519 N=16 bash scripts/runpod/pull_parallel.sh /workspace/volume/train.bin /workspace/volume/train.bin
set -e
SRC="$1"; DST="$2"; N="${N:-16}"
SSH="ssh -i $KEY -p $SRC_PORT -o StrictHostKeyChecking=no -o Compression=no root@$SRC_HOST"
SIZE=$($SSH "stat -c %s $SRC")
CHUNK=$(( (SIZE + N - 1) / N ))
echo "size $SIZE bytes, $N streams of $CHUNK"
truncate -s "$SIZE" "$DST"
for i in $(seq 0 $((N-1))); do
  OFF=$(( i * CHUNK ))
  LEN=$CHUNK; [ $(( OFF + LEN )) -gt "$SIZE" ] && LEN=$(( SIZE - OFF ))
  ( $SSH "dd if=$SRC bs=4M skip=$OFF count=$LEN iflag=skip_bytes,count_bytes 2>/dev/null" \
      | dd of="$DST" bs=4M seek=$OFF oflag=seek_bytes conv=notrunc 2>/dev/null ) &
done
wait
echo "done: $(stat -c %s "$DST") bytes"

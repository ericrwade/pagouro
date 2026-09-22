#!/usr/bin/env bash
# Runs ON THE TRAINING POD after pull_parallel.sh: hash each of the N byte-ranges on both sides and
# re-fetch the ones that differ (sshd's MaxStartups drops some of N simultaneous connections; launches
# here are staggered). Repeat until every chunk matches.
#   SRC_HOST=... SRC_PORT=... KEY=... N=16 bash scripts/runpod/pull_verify_chunks.sh /workspace/volume/train.bin /workspace/volume/train.bin
set -e
SRC="$1"; DST="$2"; N="${N:-16}"
SSH="ssh -i $KEY -p $SRC_PORT -o StrictHostKeyChecking=no -o Compression=no root@$SRC_HOST"
SIZE=$(stat -c %s "$DST")
CHUNK=$(( (SIZE + N - 1) / N ))
for round in 1 2 3 4; do
  bad=()
  for i in $(seq 0 $((N-1))); do
    OFF=$(( i * CHUNK )); LEN=$CHUNK; [ $(( OFF + LEN )) -gt "$SIZE" ] && LEN=$(( SIZE - OFF ))
    L=$(dd if="$DST" bs=4M skip=$OFF count=$LEN iflag=skip_bytes,count_bytes 2>/dev/null | sha256sum | cut -c1-64)
    R=$($SSH "dd if=$SRC bs=4M skip=$OFF count=$LEN iflag=skip_bytes,count_bytes 2>/dev/null | sha256sum | cut -c1-64")
    if [ "$L" != "$R" ]; then bad+=("$i"); echo "chunk $i differs"; else echo "chunk $i ok"; fi
  done
  [ ${#bad[@]} -eq 0 ] && { echo "ALL $N CHUNKS MATCH"; exit 0; }
  echo "round $round: re-fetching ${#bad[@]} chunk(s): ${bad[*]}"
  for i in "${bad[@]}"; do
    OFF=$(( i * CHUNK )); LEN=$CHUNK; [ $(( OFF + LEN )) -gt "$SIZE" ] && LEN=$(( SIZE - OFF ))
    ( $SSH "dd if=$SRC bs=4M skip=$OFF count=$LEN iflag=skip_bytes,count_bytes 2>/dev/null" \
        | dd of="$DST" bs=4M seek=$OFF oflag=seek_bytes conv=notrunc 2>/dev/null ) &
    sleep 1
  done
  wait
done
echo "chunks still differ after 4 rounds"; exit 1

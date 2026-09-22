#!/usr/bin/env bash
# Runs ON THE TRAINING POD: pull the finished volume (train.bin / val.bin / meta.json) from the build
# pod in another datacentre over SSH, then verify byte count and sha256 against meta.json.
# The build pod must still be running; its host/port come from `get-pod` (ssh.direct), and a key it
# accepts must be at $KEY on this pod (generate one here, append its .pub to the build pod's
# ~/.ssh/authorized_keys from the desk).
#
#   SRC_HOST=157.157.221.177 SRC_PORT=34490 KEY=/root/.ssh/id_ed25519 bash scripts/runpod/pull_volume.sh
set -e
DST="${DST:-/workspace/volume}"
SRC="${SRC:-/workspace/volume}"
mkdir -p "$DST"
apt-get install -qq -y rsync > /dev/null 2>&1 || true
for f in meta.json val.bin train.bin; do
  rsync -a --partial --inplace --info=progress2 -e "ssh -i $KEY -p $SRC_PORT -o StrictHostKeyChecking=no" \
      "root@$SRC_HOST:$SRC/$f" "$DST/$f"
done
python3 - "$DST" <<'PY'
import hashlib, json, os, sys
d = sys.argv[1]; m = json.load(open(os.path.join(d, "meta.json")))
n = os.path.getsize(os.path.join(d, "train.bin")) // 2
assert n == m["train_tokens"], f"train.bin holds {n:,} tokens, meta says {m['train_tokens']:,}"
if m.get("sha256_train_bin"):
    h = hashlib.sha256()
    with open(os.path.join(d, "train.bin"), "rb") as f:
        for chunk in iter(lambda: f.read(1 << 26), b""):
            h.update(chunk)
    assert h.hexdigest() == m["sha256_train_bin"], "sha256 mismatch after copy"
    print("sha256 verified")
print(f"volume pulled and verified: {n:,} train tokens, {m['val_tokens']:,} val tokens, {len(m['shards'])} shards")
PY

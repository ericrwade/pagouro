#!/usr/bin/env bash
# Runs ON THE POD, once, after the bundle has been copied to /workspace.
# Idempotent. Torch comes with the runpod/pytorch image; only the two small
# Python deps are installed. Prints the facts the operator needs to record.
set -e
cd /workspace
mkdir -p pagouro && tar --no-same-owner -xzf pagouro-bundle.tar.gz -C pagouro
cd pagouro
python -m pip install -q --disable-pip-version-check numpy tokenizers gguf 2>&1 | tail -1 || true
echo "== gpu =="
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
python - <<'EOF'
import torch, platform
print("torch", torch.__version__, "cuda", torch.version.cuda, "available", torch.cuda.is_available())
print("device", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "-")
print("bf16 supported", torch.cuda.is_bf16_supported() if torch.cuda.is_available() else "-")
print("python", platform.python_version())
EOF
echo "== data =="
ls -la data/tokenized_real 2>/dev/null || echo "no tokenized data in bundle"
echo "setup done"

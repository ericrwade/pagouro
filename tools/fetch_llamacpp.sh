#!/usr/bin/env bash
# Fetch the pinned llama.cpp Vulkan build for Windows x64.
# Pinned deliberately: an unpinned "latest" makes results irreproducible, and this
# project is meant to be rebuildable years from now.
set -euo pipefail
BUILD="${1:-b11005}"
DIR="$(cd "$(dirname "$0")" && pwd)"
URL="https://github.com/ggml-org/llama.cpp/releases/download/${BUILD}/llama-${BUILD}-bin-win-vulkan-x64.zip"
echo "fetching llama.cpp ${BUILD} (Vulkan, win-x64)"
curl -sL -o "$DIR/llamacpp.zip" "$URL"
powershell -NoProfile -Command "Expand-Archive -Path '$DIR/llamacpp.zip' -DestinationPath '$DIR/llamacpp' -Force"
rm -f "$DIR/llamacpp.zip"
"$DIR/llamacpp/llama-cli.exe" --version 2>&1 | head -2

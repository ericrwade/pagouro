#!/usr/bin/env bash
# Pack what a rented GPU needs into one tarball: the model code, the training
# scripts, the tokenizer, and (optionally) already-tokenized data. No checkpoints,
# no raw corpus, no secrets, no .env. The pod never sees the repo's history.
#
#   bash scripts/runpod/make_bundle.sh            # code + tokenizer + data/tokenized_real
#   bash scripts/runpod/make_bundle.sh --no-data  # code + tokenizer only (pod fetches data itself)
#   bash scripts/runpod/make_bundle.sh --anneal   # + tokenized_anneal (the decay-phase data for flash.sh)
set -e
cd "$(dirname "$0")/../.."
OUT=build/bundle
mkdir -p "$OUT"
LIST="pagouro scripts/train.py scripts/train_sft.py scripts/tokenize_corpus.py scripts/fetch_data.py scripts/build_mixture.py scripts/export_gguf.py scripts/runpod/on_pod_setup.sh scripts/runpod/shakedown.sh scripts/runpod/flash.sh scripts/runpod/ddp_rehearsal.sh scripts/runpod/volume.sh scripts/runpod/train_1b.sh scripts/build_volume.py scripts/fetch_stackexchange.py scripts/fetch_wikipedia_dump.py scripts/fetch_dated_code.py plans corpus.json data/tokenizer_real/tokenizer.json data/tokenizer_real/tokenizer_config.json"
case "${1:-}" in
  --no-data)  ;;                                                   # code + tokenizer only
  --anneal)   LIST="$LIST data/tokenized_anneal" ;;                # + the domain mix for the decay phase (24 MB)
  *)          LIST="$LIST data/tokenized_real data/tokenized_anneal" ;;
esac
tar -czf "$OUT/pagouro-bundle.tar.gz" --exclude='__pycache__' $LIST
(cd "$OUT" && sha256sum pagouro-bundle.tar.gz | tee pagouro-bundle.sha256)
ls -la "$OUT/pagouro-bundle.tar.gz"

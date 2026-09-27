#!/usr/bin/env bash
# Shallow-clone pallets/flask at tag 3.1.0 into data/sample_repo
set -euo pipefail

DEST="data/sample_repo"

if [ -d "$DEST/.git" ]; then
  echo "data/sample_repo already exists, skipping clone."
  exit 0
fi

mkdir -p data
git clone --depth 1 --branch 3.1.0 https://github.com/pallets/flask "$DEST"
echo "Cloned pallets/flask @ 3.1.0 into $DEST"

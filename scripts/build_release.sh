#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
version=$(python -c 'from torch2pc_thesis import __version__; print(__version__)')
name="torch2pc-layerwise-thesis-${version}"
mkdir -p artifacts
git archive --format=zip --prefix="${name}/" \
  --output="artifacts/${name}.zip" HEAD
sha256sum "artifacts/${name}.zip" > "artifacts/${name}.zip.sha256"
printf 'Created artifacts/%s.zip\n' "$name"

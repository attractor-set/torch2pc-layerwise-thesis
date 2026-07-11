#!/usr/bin/env bash
set -euo pipefail
mkdir -p "${HOME:-/tmp/home}" /workspace/results /workspace/data /workspace/external
exec "$@"

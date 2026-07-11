#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
. ./.env
set +a

docker manifest inspect "$ROCM_PYTORCH_IMAGE" >/dev/null
printf 'Доступен образ: %s\n' "$ROCM_PYTORCH_IMAGE"

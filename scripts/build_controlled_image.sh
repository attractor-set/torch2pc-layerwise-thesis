#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -f .env ]] || { echo "Отсутствует .env; выполните make init" >&2; exit 1; }
set -a
. ./.env
set +a
if [[ "$ROCM_PYTORCH_IMAGE" != *@sha256:* ]]; then
  echo "Сначала зафиксируйте базовый образ: make pin-base-image" >&2
  exit 1
fi
commit="$(git rev-parse HEAD)"
if [[ ! "$commit" =~ ^[0-9a-f]{40}$ ]]; then
  echo "Не удалось определить полный Git commit" >&2
  exit 1
fi
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Контролируемый образ собирается только из чистого Git working tree" >&2
  exit 1
fi
python3 - "$commit" <<'INNERPY'
from pathlib import Path
import sys
path = Path(".env")
commit = sys.argv[1]
lines = path.read_text(encoding="utf-8").splitlines()
result = []
found = False
for line in lines:
    if line.startswith("SOURCE_GIT_COMMIT="):
        result.append(f"SOURCE_GIT_COMMIT={commit}")
        found = True
    else:
        result.append(line)
if not found:
    result.append(f"SOURCE_GIT_COMMIT={commit}")
path.write_text("\n".join(result) + "\n", encoding="utf-8")
INNERPY
export SOURCE_GIT_COMMIT="$commit"
docker compose build --pull validate
printf 'Собран образ для source commit %s\n' "$commit"

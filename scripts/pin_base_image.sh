#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

[[ -f .env ]] || { echo "Отсутствует .env; выполните make init" >&2; exit 1; }
set -a
. ./.env
set +a

reference="$ROCM_PYTORCH_IMAGE"
if [[ "$reference" == *@sha256:* ]]; then
  printf 'Базовый образ уже зафиксирован: %s\n' "$reference"
  exit 0
fi

docker pull "$reference"
repo="${reference%%:*}"
digest_ref="$(docker image inspect "$reference" --format '{{range .RepoDigests}}{{println .}}{{end}}' | awk -v repo="$repo" 'index($0, repo "@sha256:") == 1 {print; exit}')"
if [[ -z "$digest_ref" ]]; then
  digest_ref="$(docker image inspect "$reference" --format '{{index .RepoDigests 0}}')"
fi
if [[ ! "$digest_ref" =~ @sha256:[0-9a-f]{64}$ ]]; then
  echo "Не удалось получить immutable digest для $reference" >&2
  exit 1
fi

python3 - "$digest_ref" <<'PY'
from pathlib import Path
import sys

path = Path(".env")
digest_reference = sys.argv[1]
lines = path.read_text(encoding="utf-8").splitlines()
output = []
updated = False
for line in lines:
    if line.startswith("ROCM_PYTORCH_IMAGE="):
        output.append(f"ROCM_PYTORCH_IMAGE={digest_reference}")
        updated = True
    else:
        output.append(line)
if not updated:
    output.append(f"ROCM_PYTORCH_IMAGE={digest_reference}")
path.write_text("\n".join(output) + "\n", encoding="utf-8")
PY
printf 'Базовый образ зафиксирован в .env: %s\n' "$digest_ref"

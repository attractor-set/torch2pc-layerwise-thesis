#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

video_gid="$(getent group video | cut -d: -f3 || true)"
render_gid="$(getent group render | cut -d: -f3 || true)"
video_gid="${video_gid:-44}"
render_gid="${render_gid:-109}"

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

python3 - "$video_gid" "$render_gid" <<'PY'
from pathlib import Path
import os
import sys

path = Path(".env")
values = {}
for line in path.read_text(encoding="utf-8").splitlines():
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        values[key] = value
values["HOST_UID"] = str(os.getuid())
values["HOST_GID"] = str(os.getgid())
values["VIDEO_GID"] = sys.argv[1]
values["RENDER_GID"] = sys.argv[2]
path.write_text(
    "\n".join(f"{key}={value}" for key, value in values.items()) + "\n",
    encoding="utf-8",
)
PY

mkdir -p data external results/runs results/checkpoints results/splits
if [[ ! -x .venv/bin/python3 ]]; then
  python3 -m venv .venv
fi

PYTHON_BIN=".venv/bin/python3"

platform="$("$PYTHON_BIN" - <<'PY'
import platform
import sys

print(
    f"{sys.version_info.major}.{sys.version_info.minor}:"
    f"{platform.machine()}"
)
PY
)"

if [[ "$platform" != "3.12:x86_64" ]]; then
  printf 'Ожидалась платформа Python 3.12 / x86_64, получено: %s\n'     "$platform" >&2
  exit 1
fi

"$PYTHON_BIN" -m pip install -r requirements/torch-cpu.txt
"$PYTHON_BIN" -m pip install -r requirements/dev.txt
"$PYTHON_BIN" -m pip check

"$PYTHON_BIN" -m ruff --version
"$PYTHON_BIN" -m mypy --version
"$PYTHON_BIN" -m pytest --version

"$PYTHON_BIN" -m torch2pc_thesis.cli registry
printf 'Репозиторий инициализирован. Проверьте .env перед экспериментами.\n'

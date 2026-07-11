#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python3}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Релизный архив создается только из чистого Git working tree." >&2
  exit 1
fi

version="$(PYTHONPATH=src "$PYTHON_BIN" -c 'from torch2pc_thesis import __version__; print(__version__)')"
commit="$(git rev-parse HEAD)"
name="torch2pc-layerwise-thesis-${version}"
mkdir -p artifacts

git archive --format=zip --prefix="${name}/" \
  --output="artifacts/${name}.zip" HEAD
sha256sum "artifacts/${name}.zip" > "artifacts/${name}.zip.sha256"
"$PYTHON_BIN" - "$name" "$version" "$commit" <<'PY'
from pathlib import Path
import json
import sys
import time

name, version, commit = sys.argv[1:4]
metadata = {
    "schema_version": 1,
    "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "artifact": f"{name}.zip",
    "project_version": version,
    "source_git_commit": commit,
}
Path(f"artifacts/{name}.metadata.json").write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY
printf 'Создан релизный архив artifacts/%s.zip для commit %s\n' "$name" "$commit"

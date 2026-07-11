#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
name="${1:?milestone name required}"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python3}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Перед подготовкой freeze manifest рабочее дерево должно быть чистым." >&2
  exit 1
fi

if [[ "$name" == "pilot-freeze" ]]; then
  "$PYTHON_BIN" scripts/check_protocol_gate.py pilot
  "$PYTHON_BIN" scripts/check_pilot_freeze.py
fi

"$PYTHON_BIN" - "$name" <<'PY'
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time
import yaml

name = sys.argv[1]
files = [
    Path("configs/base.yaml"),
    *sorted(Path("configs/methods").glob("*.yaml")),
    Path("configs/stages/final.yaml"),
    Path("PREREGISTRATION.md"),
    Path("HYPOTHESES.md"),
    Path("docs/analysis-plan.md"),
]
selected = {}
for method in ["fixedpred", "strict"]:
    value = yaml.safe_load(
        Path(f"configs/methods/{method}.yaml").read_text(encoding="utf-8")
    )
    selected[method] = value["method"]
environment_lock_path = Path("results/summaries/environment-lock.json")
environment_lock = json.loads(environment_lock_path.read_text(encoding="utf-8"))
manifest = {
    "schema_version": 1,
    "milestone": name,
    "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "source_git_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip(),
    "image_source_git_commit": environment_lock.get("image_source_git_commit"),
    "environment_lock_sha256": hashlib.sha256(
        environment_lock_path.read_bytes()
    ).hexdigest(),
    "selected_method_parameters": selected,
    "files": [
        {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in files
    ],
}
out = Path(f"results/summaries/{name}_manifest.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(out)
PY

printf '%s\n' "Freeze manifest создан. Проверьте его, затем выполните:"
printf '%s\n' "git add results/summaries/${name}_manifest.json"
printf '%s\n' "git commit -m 'research: freeze pilot configuration'"
printf '%s\n' "git tag -a ${name} -m 'Research milestone: ${name}'"

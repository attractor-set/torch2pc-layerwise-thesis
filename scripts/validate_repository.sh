#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}"

python -m compileall -q src scripts
ruff check src tests scripts/*.py
mypy src
python scripts/check_epistemic_language.py
python scripts/check_language_structure.py
python scripts/check_local_links.py
python -m torch2pc_thesis.cli validate --stage smoke --method bp
python -m torch2pc_thesis.cli validate --stage pilot --method fixedpred
python -m torch2pc_thesis.cli validate --stage final --method fixedpred
python -m torch2pc_thesis.cli validate --stage final --method strict
PYTHONPATH=src pytest -q
if command -v cffconvert >/dev/null 2>&1; then
  cffconvert --validate
fi

python - <<'PY'
from pathlib import Path
import ast
import nbformat
import yaml

roots = [Path("configs"), Path(".github")]
for root in roots:
    for path in root.rglob("*.yaml"):
        yaml.safe_load(path.read_text(encoding="utf-8"))
    for path in root.rglob("*.yml"):
        yaml.safe_load(path.read_text(encoding="utf-8"))

for path in Path("src").rglob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"))
for path in Path("scripts").glob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"))
for path in Path("tests").rglob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"))

for path in Path("notebooks/analysis").glob("*.ipynb"):
    notebook = nbformat.read(path, as_version=4)
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            try:
                ast.parse(cell.source)
            except SyntaxError as exc:
                raise RuntimeError(f"{path}: cell {index}: {exc}") from exc

print("Repository validation: ok")
PY

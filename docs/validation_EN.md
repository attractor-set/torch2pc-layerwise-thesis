# Repository validation

[Русская версия](validation.md)

Checks are executed from the current Git commit. Static validation-result files
are not retained as permanent root-level claims because they become stale after
source changes.

## Local validation

```bash
source .venv/bin/activate
python3 -m ruff check src tests scripts/*.py
python3 -m mypy src
python3 -m pytest -q
python3 scripts/check_epistemic_language.py
python3 scripts/check_language_structure.py
python3 scripts/check_local_links.py
bash scripts/validate_repository.sh
```

## CI validation

GitHub Actions runs the same checks in a clean environment with dependencies
constrained by `requirements/lock-dev.txt` and `requirements/torch-cpu.txt`.

A green CI result describes a specific commit. It does not establish a research
hypothesis and does not replace Docker/ROCm execution, C0/C1, pilot, or final.

## Release metadata

`scripts/build_release.sh` creates a `git archive` package and records its
SHA-256, project version, full source commit, and metadata creation time.
Runtime experiments retain their own manifests and environment-lock binding.

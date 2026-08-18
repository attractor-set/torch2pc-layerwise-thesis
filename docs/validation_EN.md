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
python3 scripts/check_glossary_usage.py
python3 scripts/check_local_links.py
bash scripts/validate_repository.sh
```

## CI validation

GitHub Actions runs the same checks in a clean environment with dependencies
constrained by `requirements/lock-dev.txt` and `requirements/torch-cpu.txt`.

A green CI result describes a specific commit. It does not establish a research
hypothesis and does not replace Docker/ROCm [execution](glossary_EN.md#term-execution), C0/C1, pilot, or final.

## Release metadata

For `v1.0.1`, `scripts/check_release_contract.py` validates the release contract and `scripts/build_release.sh` is the release-facing builder. It
checks the release and public-surface contracts, runs `make thesis-check` and
`make thesis-all`, and then creates:

- a `git archive` source package and SHA-256 digest;
- separate `-ru.pdf` and `-en.pdf` artifacts and their SHA-256 digests;
- metadata JSON containing version and Git commit/tree identities;
- `release-manifest.json` binding asset identities, per-language page counts, and
  document gate statuses;
- release notes.

The builder requires an unchanged tracked tree and index but does not treat
local untracked scientific/[runtime](glossary_EN.md#term-runtime) [evidence](glossary_EN.md#term-evidence) as part of the public source
release. The RU/EN congruence gate checks structure, claim-status semantics,
terminology invariants, and critical numerical boundaries; equal pagination is
not required. The builder neither runs nor authorizes scientific experiments.

The GitHub workflow for tag `v1.0.1` publishes these assets as a GitHub Release
and refuses to overwrite an existing release for the same tag.

# Validation, aggregation и sealing Stage 3B B0

[English version](stage3b-b0-sealing_EN.md)

## Назначение

`scripts/seal_stage3b_b0.py` читает полный immutable archive завершённой
ROCm/float32 canonical lane. Script не изменяет archive и записывает отдельный
compact evidence bundle.

Обязательные identity inputs:

- exact execution source commit;
- exact source commit sealing implementation;
- immutable Docker image digest `sha256:<64 hex>`;
- SHA-256 файла archive `SHA256SUMS`.

## Validation gates

Pipeline проверяет:

- exact checksum inventory без missing, extra и symlink files;
- project freeze schema v2, ROCm preflight и campaign authorization;
- archived manifest и authorization snapshots;
- один завершённый canonical run;
- 96/96 completed cells, отсутствие failed attempts и systemic stop;
- отдельный child process record для каждой cell;
- request/terminal hashes и immutable fields;
- exact B0 matrix: methods, depths, widths, batch sizes и model seeds;
- 250 composite и integrity records на cell;
- 1250 region records на cell;
- completeness всех preregistered regions;
- float32 non-perturbation thresholds и отсутствие non-finite events;
- отсутствие test dataset access.

## Производные файлы

- `validation.json` — полный acceptance record;
- `metric-definitions.json` — точные aggregation definitions;
- `cell_metrics.csv` — 96 seed-level cell rows;
- `region_metrics.csv` — 480 seed-level cell-region rows;
- `paired_method_metrics.csv` — 48 FixedPred/Strict pairs;
- `configuration_metrics.csv` — 32 method/configuration summaries по трём seeds;
- `seal.json` — content-addressed evidence seal с execution и sealing source commits;
- `SHA256SUMS` — inventory производного bundle.

Nearest-rank p95 определяется как элемент с one-indexed rank
`ceil(0.95 * n)`. Peak memory — максимальное наблюдаемое значение внутри
отдельного cell child process.

## Границы утверждений

Seal разрешает публикацию только aggregate evidence B0 baseline candidate.
Он не означает завершение A0/B1/B2 или всей Stage 3B campaign. Raw archive
остаётся non-evidence execution source и не копируется в Git.

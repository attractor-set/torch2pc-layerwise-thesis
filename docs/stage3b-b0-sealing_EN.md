# Stage 3B B0 validation, aggregation, and sealing

[Русская версия](stage3b-b0-sealing.md)

## Purpose

`scripts/seal_stage3b_b0.py` reads the complete immutable archive of the
finished ROCm/float32 canonical lane. It never modifies that archive and writes
a separate compact [evidence](glossary_EN.md#term-evidence) bundle.

Required identity inputs are:

- the exact [execution](glossary_EN.md#term-execution) source commit;
- the exact sealing implementation source commit;
- the immutable Docker image digest `sha256:<64 hex>`;
- the SHA-256 of the archive `SHA256SUMS` file.

## Validation gates

The pipeline verifies:

- an exact checksum inventory with no missing, extra, or symlink files;
- the schema-v2 project freeze, ROCm preflight, and campaign authorization;
- archived manifest and authorization snapshots;
- exactly one completed canonical run;
- 96/96 completed cells, no failed attempts, and no systemic stop;
- one child-process telemetry record per cell;
- request/terminal hashes and immutable fields;
- the exact B0 method, depth, width, batch-size, and model-seed matrix;
- 250 composite and integrity records per cell;
- 1,250 region records per cell;
- completeness of all preregistered regions;
- float32 non-perturbation thresholds and zero non-finite events;
- no [test-dataset access](glossary_EN.md#term-test-dataset-access).

## Derivative files

- `validation.json` — complete acceptance record;
- `metric-definitions.json` — exact aggregation definitions;
- `cell_metrics.csv` — 96 seed-level cell rows;
- `region_metrics.csv` — 480 seed-level cell-region rows;
- `paired_method_metrics.csv` — 48 FixedPred/Strict pairs;
- `configuration_metrics.csv` — 32 three-seed method/[configuration](glossary_EN.md#term-configuration) summaries;
- `seal.json` — content-addressed [evidence](glossary_EN.md#term-evidence) seal with [execution](glossary_EN.md#term-execution) and sealing source commits;
- `SHA256SUMS` — derivative-bundle inventory.

Nearest-rank p95 uses the one-indexed rank `ceil(0.95 * n)`. Peak memory is the
maximum value observed inside the isolated child process for one cell.

## Claim boundary

The seal permits publication only for aggregate B0 [baseline](glossary_EN.md#term-baseline)-[candidate](glossary_EN.md#term-candidate)
[evidence](glossary_EN.md#term-evidence). It does not mark A0/B1/B2 or the full Stage 3B campaign complete. The
raw archive remains a non-[evidence](glossary_EN.md#term-evidence) [execution](glossary_EN.md#term-execution) source and is not committed to
Git.

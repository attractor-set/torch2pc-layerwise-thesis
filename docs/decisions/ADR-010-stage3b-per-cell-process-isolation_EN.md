# ADR-010: per-cell process isolation for Stage 3B B0 canonical execution

- Status: accepted
- Date: 2026-07-14
- Scope: Stage 3B B0 canonical execution lifecycle
- Baseline commit: `f40db15e65cb3f701711ce5b41732e9b87d6104a`

## Context

The ROCm/float32 canonical protocol contains 96 cells. The previous runner executed them sequentially in one Python process. Fresh-process heavy FixedPred and Strict cells reserved approximately 310–312 MiB of VRAM, while the shared process retained approximately 11.5 GiB after 16 completed cells. The first HIP `OutOfMemoryError` did not stop the lane, so 80 additional failed attempts were created.

This is an execution-lifecycle and GPU-runtime ownership defect. It does not change the Stage 3B protocol contract, scientific measurements, or Stage 3A evidence.

## Decision

The production canonical lane performs the following sequence for every selected cell:

1. The parent controller stores immutable authorization and manifest snapshots in the unique run directory.
2. The parent starts a fresh Python interpreter with `python -m torch2pc_thesis.stage3b_canonical_child`.
3. The child re-verifies authorization and the canonical lane, executes exactly one cell through the existing `execute_canonical_cell()`, and exits.
4. The parent identifies exactly one new attempt directory and accepts exactly one terminal record: `completed.json` or `failed.json`.
5. The parent verifies identity, authorization token, manifest digest, source commit, lane, image digest, canonical protocol, attempt id, and attempt directory.
6. The parent records the terminal SHA-256 and process telemetry: parent PID, child PID, exit code, timestamps, stdout/stderr digests, and bounded tails.
7. The parent starts the next cell only after terminal validation succeeds.

Each production cell receives a separate Python/HIP context. Child-process termination is the boundary for releasing process-owned GPU allocations; `torch.cuda.empty_cache()` is not used as a substitute for process isolation.

## Fail-fast policy

A validated failed terminal is classified as a systemic resource failure when any of the following is observed:

- `OutOfMemoryError`;
- `HIP out of memory`;
- `CUDA out of memory`;
- an equivalent HIP/CUDA allocation error.

After the first such event, the parent ends the cell loop. The current failed cell keeps one attempt; all later cells remain pending and receive no attempts. The lane records `lane_incomplete`, `stopped_early=true`, and a `systemic_stop` record linked to the original failure.

An ordinary independent cell failure keeps the previous policy: its failed terminal is recorded and the parent may continue with later cells.

## Interruption and resume

When the child or parent is interrupted after `started.json` and before a terminal record, the attempt remains running. The existing planner rejects a later run without `--resume`. Explicit `--resume` makes that attempt retryable within `max_attempts`.

A missing or invalid terminal record is a lifecycle violation. The parent records available process telemetry, aborts the lane, and does not start the next cell.

## Canonical boundaries

- Production canonical execution remains limited to `rocm/float32`.
- The internal child also rejects CPU/float64.
- CPU/float64 remains available only to bounded smoke and injected engineering-control tests.
- The canonical protocol remains 96 cells, 20 warm-up steps, 50 measured steps, and 5 repetitions.
- `evidence=false`, publication disabled, and test dataset inaccessible remain unchanged.
- Stage 3A artifacts and checksums remain unchanged.

## Consequences

Benefits:

- VRAM lifetime is bounded to one cell;
- cross-cell allocator retention is removed;
- OOM produces one fail-fast event rather than a cascade of attempts;
- process → attempt → terminal provenance is auditable;
- existing lock, plan, retry, and resume semantics are retained.

Costs:

- one interpreter startup per cell;
- additional run-local snapshots and process telemetry records;
- the production runner requires the current package to be importable by the same Python executable.

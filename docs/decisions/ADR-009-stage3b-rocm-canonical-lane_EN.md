# ADR-009: ROCm/float32 as the only Stage 3B B0 canonical lane

[Русская версия](ADR-009-stage3b-rocm-canonical-lane.md)

- Status: accepted corrective protocol decision;
- date: 2026-07-14;
- scope: Stage 3B B0 profiling;
- changes Stage 1/2 or published Stage 3A evidence: no.

## Context

The preregistered Stage 3 profiling matrix contains 336 cells, including 96 B0 `stage2_baseline` cells. Device is not an additional matrix axis. Duplicating every B0 cell on CPU and ROCm would create 192 B0 executions and 672 Stage 3 executions, which is outside the frozen design.

CPU/float64 had previously served as an engineering correctness/control environment for smoke, non-perturbation, and targeted equivalence gates. It was incorrectly promoted to a second mandatory canonical performance lane in campaign authorization.

The erroneous CPU lane was terminated by the memory-cgroup OOM killer after 21 completed cells and one interrupted attempt. The Python process had approximately 50,202,008 KiB anonymous RSS when killed. All CPU attempts remain immutable, are classified with `evidence=false` and `full_lane_complete=false`, and are excluded from confirmatory results.

## Decision

1. The only canonical B0 performance lane is `rocm/float32`.
2. The canonical design contains exactly 96 executions: 48 FixedPred and 48 Strict.
3. The canonical protocol remains `20 warm-up × 50 measured × 5 repetitions`.
4. `cpu/float64` remains an engineering control lane for bounded smoke and targeted equivalence checks only.
5. CPU control does not contribute to `full_lane_complete`, `full_campaign_complete`, or confirmatory performance evidence.
6. Authorization requires exactly one canonical preflight: ROCm/float32. A CPU preflight may be attached only as an optional engineering-control record.
7. The canonical CLI rejects CPU before creating a lock, lane directory, or attempt.
8. The machine-readable source of truth is `experiments/planned/STAGE3B-B0-PROTOCOL-CONTRACT.json`.
9. Authorization moves to schema version 2 with a new domain and scope; version 1 and the previous two-lane token are retired and cannot be resumed.

## Consequences

After merge, the campaign requires a new project freeze, image digest, output root, ROCm preflight, and authorization token. The previous CPU attempts and token remain as an audit trail but are not used for scientific claims.

Stage 3A results, SHA manifests, B0 manifest ordering, seeds, methods, depth/width/batch grid, and the Torch2PC source commit remain unchanged.

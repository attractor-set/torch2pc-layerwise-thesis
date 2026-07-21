# ADR-025: Stage 3B matched-profiling request refreeze

[Русская версия](ADR-025-stage3b-matched-profiling-request-refreeze.md)

- **Status:** accepted
- **Date:** July 20, 2026

## Context

The historical `v1` request and manifest were built from B1 and B2 smoke
decisions. After sealed confirmatory `EQ-B1` and `EQ-B2` were published, that
opening does not gain retrospective admission and remains byte-identical.

## Decision

Create a new append-only package:

```text
experiments/frozen/stage3b-matched-profiling-v2/
  SHA256SUMS
  manifest.json
  request.json
```

`request.json` prospectively references the sealed confirmatory `EQ-B1` and
`EQ-B2` admissions, records historical `v1` by SHA-256, and forbids
retrospective admission. `manifest.json` preserves the registered 288-cell
matrix, exact order counterbalance, and closed test split.

## Boundary

```text
scientific_admission=open
matched_profiling_request_refrozen=true
matched_profiling_request_refresh_required=false
matched_profiling_execution_open=false
runtime_authorization=not_issued
measurements_allowed=false
test_dataset_access=false
```

The refreeze creates no [runtime](../glossary_EN.md#term-runtime)
authorization, measurements, or [evidence](../glossary_EN.md#term-evidence).
The next admissible transition is a separate immutable image, ROCm preflight,
authorization, and non-measuring dry-run gate sequence. Only then may the
288-cell campaign be authorized.

## Consequences

- the confirmatory B1/B2 admission chain becomes the production-prelaunch input;
- historical `v1` artifacts remain verifiable and immutable;
- runner and runtime scripts default only to the `v2` package;
- `EX-IF0`, estimator, `QWake-PC`, offline policy, and the test split remain closed.

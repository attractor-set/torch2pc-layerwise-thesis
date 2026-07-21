# Architecture and research decisions

[Русская версия](index.md)

- ADR-001: Use Torch2PC as the primary implementation.
- ADR-002: Use native Ubuntu and ROCm Docker for final results.
- ADR-003: Use macro F1 as the primary selection metric.
- ADR-004: Use paired multi-seed statistics with Holm correction.
- ADR-005: Freeze post-pilot final ordering, resumption, and telemetry.
- [ADR-006](ADR-006-stage3-scope_EN.md): extended Stage 3 scope.
- [ADR-007](ADR-007-stage3-locality-taxonomy_EN.md): multidimensional locality taxonomy.
- [ADR-008](ADR-008-predict-correct-acceleration_EN.md): predict-correct acceleration and exact-correction boundaries.
- [ADR-009](ADR-009-stage3b-rocm-canonical-lane_EN.md): ROCm/float32 as the only Stage 3B B0 canonical lane; CPU/float64 remains an engineering control.
- [ADR-010](ADR-010-stage3b-per-cell-process-isolation_EN.md): a fresh Python child process per Stage 3B B0 canonical cell with fail-fast handling for systemic OOM.
- [ADR-011](ADR-011-stage3b-b0-derived-evidence-seal_EN.md): read-only validation, aggregation, and a content-addressed Stage 3B B0 [evidence](../glossary_EN.md#term-evidence) seal.
- [ADR-012](ADR-012-pc-tref-pc-catm-scenario-a_EN.md): PC-TREF Balanced Core, PC-CATM, and Scenario A as one realistic post-B0 path.
- [ADR-013](ADR-013-pc-tref-operational-semantics_EN.md): operational `PC-TREF`/`PC-CATM` semantics, separate cost boundaries, and B1/B2 admission to preregistration.
- [ADR-014](ADR-014-stage3b-b1-b2-candidate-contracts_EN.md): separate exact
  implementation contracts and equivalence gates for B1/B2.
- [ADR-015](ADR-015-stage3b-matched-measurement-sealing_EN.md): separated
  primary timing and structural counters, locality event streams, and
  matched-specific evidence sealing.
- [ADR-016](ADR-016-stage3b-sufficiency-boundary_EN.md): the one-step
  [operational sufficiency boundary](../glossary_EN.md#term-operational-sufficiency-boundary), separation of oracle label and pre-action
  estimator, conditional geometry, and the unchanged post-`EX-IF0` admission sequence.
- [ADR-017](ADR-017-stage3b-288cell-correctness-repair_EN.md): fail-closed
  lifecycle, confirmatory admission, exact counterbalance, and
  cross-[candidate](../glossary_EN.md#term-candidate) correctness repair before
  the 288-cell campaign.
- [ADR-018](ADR-018-stage3b-b1-confirmatory-preregistration_EN.md): freezes confirmatory `EQ-B1` as 120 matched pairs over ten distinct validation batches and keeps [execution](../glossary_EN.md#term-execution) closed pending a separate opening review.
- [ADR-019](ADR-019-stage3b-b1-confirmatory-opening_EN.md): adds fail-closed
  batch freezing, two-lane authorization, recovery, and confirmatory `EQ-B1`
  sealing infrastructure while keeping [runtime](../glossary_EN.md#term-runtime) execution closed.
- [ADR-020](ADR-020-pc-multiscale-mechanism-decision-architecture_EN.md): [multiscale mechanism–decision architecture](../glossary_EN.md#term-multiscale-mechanism-decision-architecture), scale-specific contracts, and the boundary of the future `QWake-SPC` line.
- [ADR-021](ADR-021-stage3b-b2-confirmatory-preregistration_EN.md): freezes confirmatory `EQ-B2` as 120 matched triples and 240 direct comparisons, reuses the frozen B1 inputs, and keeps [execution](../glossary_EN.md#term-execution) and [matched profiling](../glossary_EN.md#term-matched-profiling) closed pending separate admission.
- [ADR-022](ADR-022-stage3b-b2-confirmatory-opening_EN.md): adds fail-closed request freezing, separated authorization, recovery, and confirmatory `EQ-B2` sealing infrastructure while keeping [execution](../glossary_EN.md#term-execution) closed pending a separate request freeze and runtime admission.
- [ADR-023](ADR-023-stage3b-b2-confirmatory-request-freeze_EN.md): freezes the append-only confirmatory `EQ-B2` request for 120 triples/240 comparisons while keeping [execution](../glossary_EN.md#term-execution) closed pending separate image and [runtime](../glossary_EN.md#term-runtime) validation.
- [ADR-024](ADR-024-stage3b-b2-confirmatory-evidence-preservation_EN.md): preserves byte-for-byte sealed `EQ-B2-CONFIRMATORY=pass` and derived `EQ-B2`, completes the B1/B2 scientific-admission chain, and keeps matched profiling closed until a new versioned freeze.

- [ADR-025](ADR-025-stage3b-matched-profiling-request-refreeze_EN.md): creates a new `v2` request/manifest freeze from sealed confirmatory B1/B2 admissions, preserves historical `v1`, and keeps runtime execution closed.

- [ADR-026](ADR-026-stage3b-matched-profiling-evidence-preservation_EN.md): preserves the sealed 288-cell matched-profiling evidence byte-for-byte, keeps analysis closed, and introduces a draft-only release with separate run artifacts.

- [ADR-027](ADR-027-stage3b-matched-descriptive-analysis-protocol_EN.md): freezes the post-collection/pre-analysis descriptive protocol, `model_seed` independent unit, aggregation order, seven-dimensional Pareto rule, and closed execution/publication boundary.
- [ADR-028](ADR-028-stage3b-matched-descriptive-analysis-implementation_EN.md): replaces the early analyzer with the registered 18-output engine, freezes full synthetic validation, and keeps sealed-evidence execution closed pending a separate authorization.

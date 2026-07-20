# ADR-021: confirmatory `EQ-B2` preregistration

[Русская версия](ADR-021-stage3b-b2-confirmatory-preregistration.md)

- Status: accepted
- Date: 2026-07-20

## Context

[ADR-017](ADR-017-stage3b-288cell-correctness-repair_EN.md) requires a
confirmatory `EQ-B2` with `120/120` matched triples and `240/240` registered
pairwise comparisons before production [execution](../glossary_EN.md#term-execution)
of shared [matched profiling](../glossary_EN.md#term-matched-profiling). The completed B2 control has engineering scope:
`12` triples and `24` comparisons. It validates the harness but does not meet
the production-admission requirement.

Confirmatory `EQ-B1` is already sealed with `120/120` pairs,
`scope=confirmatory`, and `status=pass`. B2 preregistration may therefore open,
while B2 execution remains closed.

## Decision

1. Confirmatory B2 is frozen as:

   ```text
   2 lanes × 2 methods × 3 model seeds × 10 validation batches = 120 triples
   ```

2. Every triple restores one common `snapshot` for `stage2_baseline`,
   `isolated_layer_vjp`, and `composite_vjp`.
3. Every triple requires two comparisons:
   `stage2_baseline ↔ composite_vjp` and
   `isolated_layer_vjp ↔ composite_vjp`, for `240` comparisons in total.
4. The exact ten validation batches and three checkpoints frozen by
   confirmatory B1 are reused. New data selection, batch mutation, and test
   split access are prohibited.
5. Numerical thresholds, state restoration, method controls, and optimizer
   settings are inherited without retuning from the existing B1/B2 contracts.
6. Primary numerical and trajectory equivalence uses `no_hooks`. A separate
   `counters_only` structural replay cannot replace primary equivalence.
7. [Attempt](../glossary_EN.md#term-attempt) history is append-only. Retry is
   allowed only after registered infrastructure, operator, or system
   interruption; scientific, correctness, provenance, and unknown failures are
   non-retryable.
8. The scientific decision identifier is `EQ-B2-CONFIRMATORY`. A positive
   decision requires `120/120` triples, `240/240` comparisons, zero failed
   pairs, all gates, `sealed=true`, and `status=pass`.
9. A separate derived `EQ-B2` admission record with `scope=confirmatory` must
   be created after a positive decision. Only then may a new versioned
   matched-profiling request/manifest freeze be created.
10. The existing smoke decision and previous 288-cell request remain immutable
    historical artifacts. They are not modified and do not authorize
    production launch.

## Stage boundary

This ADR and its contract freeze design only. They do not create a frozen
request, build an immutable image, issue [runtime](../glossary_EN.md#term-runtime) authorization, start
measurements, or create results.

A positive `EQ-B2-CONFIRMATORY` opens only a new scientific-admission freeze
for [matched profiling](../glossary_EN.md#term-matched-profiling). Execution of
the 288-cell campaign still requires separate image freeze, preflight,
authorization, and dry-run on an empty output root.

## GO criterion

The B2 execution-opening branch may begin only after the preregistration
contract passes, the B1 decision/admission and all reused input artifacts match
their SHA-256 digests, the test split remains closed, and the worktree contains
no B2 confirmatory results.

# ADR-018: confirmatory EQ-B1 preregistration

[Русская версия](ADR-018-stage3b-b1-confirmatory-preregistration.md)

## Context

[ADR-017](ADR-017-stage3b-288cell-correctness-repair_EN.md) closed production
[matched profiling](../glossary_EN.md#term-matched-profiling) until
confirmatory `EQ-B1` and `EQ-B2` [evidence](../glossary_EN.md#term-evidence)
exists. The existing B1 smoke covers 12 matched pairs and remains engineering
evidence that the harness works, but it does not satisfy the production
`120/120` admission requirement.

## Decision

Confirmatory B1 is frozen as 120 matched pairs:

```text
2 lanes × 2 methods × 3 model seeds × 10 validation batches = 120 pairs
```

The lanes remain `cpu_float64` and `rocm_float32`; methods are `FixedPred` and
`Strict`; [model seed](../glossary_EN.md#term-model-seed) values are `0`, `1`, and
`2`. Model seed remains the independent analysis unit. Pair, batch, layer,
sweep, and tensor component are nested units and must not be interpreted as 120
independent observations.

The ten batches must be ten distinct full batches with indices `0..9` from the
deterministic validation loader with `shuffle=False`. The same batch must not be
stored under multiple indices. Every batch is selected before [execution](../glossary_EN.md#term-execution),
stored as a separate artifact, and receives its own manifest and SHA-256. The
same ten batches are shared across model seeds, methods, and lanes. The test
split is neither created nor read.

Every pair restores the same reference and [candidate](../glossary_EN.md#term-candidate)
snapshot: parameters, buffers, beliefs, optimizer, RNG, and batch. Thresholds,
optimizer, and registered components are inherited unchanged from
`STAGE3B-B1-CONTRACT.json`.

## Lifecycle

[Attempt](../glossary_EN.md#term-attempt) history is append-only. At most two
attempts are permitted per pair. A retry is allowed only after infrastructure,
operator-interruption, or system-interruption failure. Correctness, scientific,
provenance, and unknown failures are non-retryable and block sealing.

The final decision requires exactly 120 completed pairs, zero failed pairs, no
running attempts, one admissible completed attempt per pair, and passing
`STRUCT-B1`, `NUM-B1`, `TRAJ-B1`, `OBS-B1`, `PROV-B1`, and `EQ-B1` gates.

## Stage boundary

This ADR freezes the design and does not open
[execution](../glossary_EN.md#term-execution). Validation-batch artifacts, the
frozen request, immutable image, [runtime](../glossary_EN.md#term-runtime)
authorization, and results are not part of the preregistration commit. They may
be created only in a later implementation/opening branch with a separate
review.

A positive confirmatory `EQ-B1` opens only confirmatory B2 preregistration and
execution. It does not by itself open 288-cell profiling, `EX-IF0`, or an
active policy.

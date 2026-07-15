# ADR-006: extended Stage 3 scope

[Русская версия](ADR-006-stage3-scope.md)

- Status: accepted for design
- Date: 2026-07-13
- Decision point: after Stage 2 completion/publication and before Stage 3 implementation

## Context

Stage 2 retained quality and reduced PC [runtime](../glossary_EN.md#term-runtime), while the remaining order was
`BP ≈ Exact < FixedPred << Strict`. One year remains for the master's thesis.
Further implementation tuning alone would have limited additional scientific
scope.

## Decision

Stage 3 covers three connected axes:

1. mathematical and [execution](../glossary_EN.md#term-execution) locality;
2. exact implementation-preserving VJP organization;
3. controlled approximations through adaptive stopping and periodic VJP refresh.

Fixed random feedback is conditional exploratory work. Mixed precision,
quantization, surrogate derivatives, asynchronous inference, and
`torch.compile` are outside the v1 core scope.

Stage 3 does not rerun Stage 1/2. Their publication states are historical
baselines, while Stage 3 receives a separate provenance chain.

## Consequences

The core scope remains feasible within one year, exact and approximate claims
remain separate, a diagnostics executor becomes mandatory, final test remains
closed until Stage 3 freeze, and rejected candidates still contribute [profiling](../glossary_EN.md#term-profiling),
locality, and [scaling](../glossary_EN.md#term-scaling) observations.

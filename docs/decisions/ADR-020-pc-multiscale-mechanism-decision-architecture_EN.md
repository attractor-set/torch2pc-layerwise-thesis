# ADR-020: multiscale mechanism–decision architecture and QWake-SPC boundary

[Русская версия](ADR-020-pc-multiscale-mechanism-decision-architecture.md)

## Status

Accepted as a theoretical and design-level extension; experimental
[execution](../glossary_EN.md#term-execution) is not permitted.

## Context

`PC-TREF`, `PC-CATM`, and `QWake-PC` are already separated as a theoretical
framework, mechanism model, and controller family. A formal description is
needed for repeating this logic across block, layer, and network scales without
claiming unverified scale invariance or expanding the mandatory master's-thesis
scope into a spiking neural network.

## Decision

Adopt the [multiscale mechanism–decision architecture](../glossary_EN.md#term-multiscale-mechanism-decision-architecture)
as a prospective compositional model:

```text
PC-CATM[scale]
→ PC-TREF sufficiency[scale]
→ QWake-PC(scale, action, budget)
→ exact verification or escalation
```

State, norm, aggregation, diagnostic representation, actions, regret, cost, and
verification are defined separately for every scale. Cross-scale transfer
requires measurement of the
[correction-composition defect](../glossary_EN.md#term-correction-composition-defect).

The current [QWake-PC](../glossary_EN.md#term-qwake-pc) preserves continuous states and errors. Its
[spike-like control dynamics](../glossary_EN.md#term-spike-like-control-dynamics)
refer to thresholded and temporally sparse organization of correction events.

[`QWake-SPC`](../glossary_EN.md#term-qwake-spc) is frozen only as the name of a
possible PhD research line in which qualified events become native spikes. This
line is not part of the current execution plan.

## Consequences

- the B1/B2, `matched profiling`, `EX-IF0`, `passive diagnostics`, `offline
  screening`, and `shadow QWake-PC` sequence is unchanged;
- `A-Core` does not require a multiscale or spike-native controller;
- an available block/layer pilot may only be a separate exploratory stage;
- local action, scale-invariance, and spike-native claims require separate
  preregistration and `evidence`;
- a negative result for a future controller does not change the status of
  `PC-TREF`, `PC-CATM`, or passive observations.

## Boundary

This ADR does not modify frozen contracts, requests, `evidence`, manifests, or the
test-split policy and does not permit `local_sweep`, `layer_sweep`, active
control, or `QWake-SPC` execution; `fallback_exact` remains the conservative reserve path.

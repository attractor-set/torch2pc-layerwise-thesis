# ADR-015: one-sided cheap ECZ/NCZ certificates

[Русская версия](ADR-015-stage3b-cheap-diagnostic-certificates.md)

Normative terms: [execution](../glossary_EN.md#term-execution),
[evidence](../glossary_EN.md#term-evidence),
[candidate](../glossary_EN.md#term-candidate),
[passive diagnostics](../glossary_EN.md#term-passive-diagnostics),
[canonical correction channel](../glossary_EN.md#term-canonical-correction-channel),
[correction geometry](../glossary_EN.md#term-correction-geometry),
[matched profiling](../glossary_EN.md#term-matched-profiling),
[device time](../glossary_EN.md#term-device-time),
[saved tensors](../glossary_EN.md#term-saved-tensors),
[observer cost](../glossary_EN.md#term-observer-cost),
[cost vector](../glossary_EN.md#term-cost-vector),
[decision regret](../glossary_EN.md#term-decision-regret),
[exact-implementation freeze](../glossary_EN.md#term-exact-implementation-freeze),
[local predictor](../glossary_EN.md#term-local-predictor), and
[shadow mode](../glossary_EN.md#term-shadow-mode).

## Status

Accepted as a design-only decision. Implementation, data collection, and
execution control remain closed.

## Context

`ECZ` and `NCZ` can have a small resultant correction while differing in the
activity of canonical correction channels. The full observer computes all
required channel-level quantities, but future passive diagnostics may
sometimes make a reliable mechanism decision from a sufficient bound or
witness.

The original “combing” metaphor described only the type of cheap test.
Topology is not part of the PC-CATM claim and is not added to the research.

## Decision

1. Cheap diagnostics are represented as a **one-sided certificate**, not as an
   approximation of every exact quantity.
2. `mechanism_label` and `certificate_status` are separate fields.
3. ECZ may be certified by a positive activity witness with a small resultant
   and passing geometry guards.
4. NCZ requires an upper bound for every relevant channel; failure to find
   activity is insufficient.
5. `abstained` is a mandatory permitted outcome.
6. Every certificate has `action_permission=none` until separate EX-IF0,
   predictor/controller preregistration, exact verification, and regret gate.
7. Observer cost belongs to the full cost vector.
8. Implementation is not added to the clean B0/B1/B2 matched-profiling timing
   lane.

Normative details: [cheap diagnostic certificates](../cheap-diagnostic-certificates_EN.md).

## Consequences

- ECZ and NCZ can be studied without requiring a cheap reconstruction of the
  exact total channel activity.
- Coverage and selective error become the certificate evaluator's primary
  metrics.
- False NCZ and false ECZ are evaluated separately.
- Ambiguous states are routed to the exact observer/[fallback](../glossary_EN.md#term-fallback).
- Diagnostic savings are counted only after observer overhead.
- A certificate does not become a stop/locality rule without action-value
  evidence.

## Rejected alternatives

### Topological explanation

Rejected as unrelated to the required cheap test and as an unnecessary
theoretical claim.

### Forced binary ECZ/NCZ classification

Rejected: lack of a sufficient witness/bound must produce `abstained`.

### `NCZ → stop` and `ECZ → continue/local sweep`

Rejected: a mechanism label does not determine expected action utility or
regret.

### Mandatory estimation of full $A_l$

Rejected as unnecessary: a sufficient certificate can resolve some
observations without exactly reconstructing $A_l$.

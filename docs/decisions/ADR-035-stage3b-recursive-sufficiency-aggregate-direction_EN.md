# ADR-035: primary recursive sufficient-aggregate direction

[Русская версия](ADR-035-stage3b-recursive-sufficiency-aggregate-direction.md)

- **Status:** accepted as a design-only direction
- **Date:** 2026-07-22

## Context

ADR-020 froze the
[multiscale mechanism–decision architecture](../glossary_EN.md#term-multiscale-mechanism-decision-architecture)
as a prospective extension and did not make it mandatory for `A-Core`.
Completed B1/B2 work and the sealed matched analysis now provide a more precise
premise: registered numerical equivalence does not guarantee equal cost
vectors. At the same time, B1/B2 did not qualify a new exact
[candidate](../glossary_EN.md#term-candidate) as a mandatory replacement for B0.

The next research line should therefore investigate existence of minimum
task-relative sufficient compute aggregates rather than another static sweep
implementation, and test whether one normative mechanism can be reused across
scales.

## Decision

1. Adopt the [minimum sufficient compute aggregate](../glossary_EN.md#term-minimum-sufficient-compute-aggregate) as the central empirical object after the publication gate and `EX-IF0`.
2. Freeze the central question in `docs/stage3b-recursive-sufficiency-aggregate-direction_EN.md`.
3. Represent stop, partial sweep, and full sweep as the empty, intermediate, and maximum elements of one nested aggregate family.
4. Do not introduce a separate `GLOBAL` policy action; a full exact sweep remains the maximum root aggregate, exact reference, and fail-closed [fallback](../glossary_EN.md#term-fallback).
5. Before controller implementation, test `E2`, `E3`, `E5`, and `P0`.
6. Validate the same normative semantics at a minimum of two scales: layers within a block and blocks within the network.
7. Retain temperature only as a transform of a conservative sufficiency-margin estimate.
8. Keep a spike-like accumulator off the critical path. Hysteresis and fuller spike-like stabilization are admissible only after measured chattering.
9. Keep the B1/B2 publication gate as the next formal transition. This ADR does not open `EX-IF0`, [execution](../glossary_EN.md#term-execution), the test split, or active policy control.

## Rationale

This decision converts a negative exact-candidate engineering result into a
positive premise for the next question without exceeding the [evidence](../glossary_EN.md#term-evidence) boundary:

```text
numerical equivalence with cost non-invariance
→ oracle sufficient-aggregate existence
→ state dependence
→ diagnostic sufficiency
→ shadow controller
```

One recursive contract reduces the number of unrelated policies and expresses
stopping, locality, and full exact computation as cases of one aggregate order.
Numerical norms and thresholds remain scale-specific and require separate
validation.

## Consequences

- ADR-020's statement that multiscale work is only an optional pilot is superseded for the post-B1/B2 research priority;
- all other ADR-020 boundaries remain: no automatic scale invariance, no spike-native claim, and no execution permission;
- B0 remains the exact reference pending a separate `EX-IF0`;
- B3, compiler studies, online reinforcement learning, and contextual bandits leave the critical path;
- failure of `E2`, `E3`, `E5`, or `P0` is admissible and narrows the subsequent scope;
- sealed B1/B2 [evidence](../glossary_EN.md#term-evidence) and generated output remain unchanged.

## Rejected alternatives

- **Implement [QWake-PC](../glossary_EN.md#term-qwake-pc) immediately.** The existence of an adaptive-choice object has not been established.
- **Use `GLOBAL` as a separate categorical action.** Full exact computation is already the maximum aggregate.
- **Treat B1/B2 as proof that a controller is necessary.** They establish only cost non-invariance for the studied exact procedures.
- **Make spike-like dynamics the central contribution.** Chattering has not been measured and basic hysteresis may suffice.
- **Enumerate every layer subset.** An exponential action space is outside the minimal confirmatory scope.

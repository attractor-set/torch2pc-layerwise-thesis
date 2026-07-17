# ADR-014: separate B1/B2 contracts and sequential admission

[Русская версия](ADR-014-stage3b-b1-b2-candidate-contracts.md)

- **Status:** accepted
- **Date:** 2026-07-16
- **Basis:** `stage3b-pc-tref-pc-catm-theory-v1`

## Context

`SI-MA1` and ADR-013 closed the prerequisite for [candidate](../glossary_EN.md#term-candidate)-specific B1/B2
preregistration, but the broad Stage 3B design did not separately freeze full-
trajectory equivalence, the direct B1/B2 control, or the boundary to future
`QWake-PC`.

## Decision

1. B1 and B2 receive separate paired documents and JSON contracts.
2. B1 is frozen as `isolated_layer_vjp` and is implemented first.
3. B2 is frozen only as `composite_vjp` and remains closed until sealed
   `EQ-B1`.
4. Block/chunk composite requires a new protocol.
5. Zero dangerous admissions are permitted; cost cannot compensate for
   numerical or safety failure.
6. Primary `no_hooks` timing and structural `counters_only` are separate
   measurement lanes; [observer cost](../glossary_EN.md#term-observer-cost) is reported separately.
7. B1/B2 define no estimator, oracle, cheap diagnostic loop, hysteresis, or
   offline policy selection.
8. `stop`, `native_one`, and `exact_one` may appear only after `EX-IF0` as
   policy-neutral counterfactual labels.
9. Offline screening, the predictor, and hysteresis require separate
   preregistrations after `A11-OFF0`/`A11-OFF1`.

## Consequences

After the publication tag, only B1 implementation is authorized. Full
[matched profiling](../glossary_EN.md#term-matched-profiling), `EX-IF0`, active control, and test access remain closed until their
own immutable decision artifacts. Scientific failure is retained as a result.

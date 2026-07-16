# ADR-013: operational `PC-TREF`/`PC-CATM` semantics and B1/B2 admission

[Русская версия](ADR-013-pc-tref-operational-semantics.md)

## Status

Accepted as a theoretical and methodological decision after final `SI-MA1`
publication. The decision permits B1/B2 preregistration preparation but does
not permit implementation or [execution](../glossary_EN.md#term-execution) without separate contracts.

## Context

`ADR-012` froze `PC-TREF`, `PC-CATM`, and Scenario A as the post-B0 design path.
`SI-MA0` and `SI-MA1` were then completed:

- `SI-MA0` retained a negative `COST-MA0` result while its other registered
  gates passed;
- `SI-MA1` passed observer-calibrated `CAL-COST-MA1` across ten `model_seed`
  units;
- the final decision artifact explicitly required a separate theoretical patch
  before B1/B2.

Exact equality of continuous features was too strict, while threshold
proximity without a transitivity qualification would be insufficient for a
literal quotient claim. Diagnostic mechanism, observer, and future control
plane also required separate cost semantics.

## Decision

1. Retain exact partition-based $\sim_I^q$ as the [diagnostic quotient](../glossary_EN.md#term-diagnostic-quotient) basis.
2. Add operational indistinguishability
   $d_I(\phi_I(x),\phi_I(y))\leq\varepsilon_I$ without assuming transitivity.
3. Define [required equivalence](../glossary_EN.md#term-required-equivalence) through registered decision classes validated
   against regret tolerance $\delta_R$.
4. Define the exact
   [task-relative equivalence defect](../glossary_EN.md#term-task-relative-equivalence-defect)
   as
   $E_I^q\setminus E_R^q$ and the separate operational safety defect as
   $E_I^q\setminus A_R^{\delta}$.
5. Add [precision-masked zero](../glossary_EN.md#term-precision-masked-zero) with explicit space, norm, scale, dtype, threshold,
   layer, step, and aggregation rule.
6. Require explicit norm contracts for every `PC-CATM` indicator.
7. Represent computational cost as a vector and preregister scalarization or a
   Pareto decision rule.
8. Separate [diagnostic-mechanism cost](../glossary_EN.md#term-diagnostic-mechanism-cost), [observer cost](../glossary_EN.md#term-observer-cost), and [control-plane cost](../glossary_EN.md#term-control-plane-cost).
9. Interpret negative `D_seed` as over-closure of the registered observer
   calibration, not negative physical cost.
10. Mark the B1/B2 theoretical prerequisite as satisfied after publication of
    this decision; permit preregistration while keeping implementation and
    execution closed until [candidate](../glossary_EN.md#term-candidate)-specific gates exist.

## Consequences

- `SI-MA0` and `SI-MA1` remain unchanged and are not retrospectively merged;
- B1/B2 receive explicit semantics for safety, regret, cost, and equivalence;
- quotient claims require an explicit partition map;
- future `ECZ` evaluator and action-selection cost are measured separately;
- negative or mixed B1/B2 outcomes remain valid results;
- the test split remains closed.

## Claim boundaries

This decision is a theoretical freeze. It does not establish B1/B2 speedup,
representation minimality, active-control safety, or transfer beyond the
registered scope.

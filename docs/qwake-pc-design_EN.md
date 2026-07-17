# Hierarchical QWake-PC design

[Русская версия](qwake-pc-design.md)

## Status and scope

This document describes future policy [architecture](glossary_EN.md#term-architecture) after `EX-IF0`. It is not a
controller preregistration, does not permit [execution](glossary_EN.md#term-execution), and does not modify B1
`isolated_layer_vjp`, B2 `composite_vjp`, or
`stage3b-b1-b2-prereg-v1`.

Until separate preregistration and positive shadow [evidence](glossary_EN.md#term-evidence),
`controls_execution=false`.

## Action hierarchy

The future controller considers an ordered ladder:

```text
stop
→ local_sweep(block_id)  # ECZ-targeted local sweep
→ full_exact             # full exact sweep
→ fallback_exact
```

`fallback_exact` is an emergency safety action rather than a savings
[candidate](glossary_EN.md#term-candidate). The controller is not required to select a local sweep: under
insufficient evidence it escalates to a full exact sweep.

## Inputs and state boundaries

Inputs are frozen in a separate contract and may include:

- PC-TREF representation $\phi_k$;
- PC-CATM geometry, transport, layer, and sweep features;
- temporal history and uncertainty;
- complete feature-computation cost;
- an eligibility mask for local blocks.

The predictor and controller do not modify `beliefs` in [shadow mode](glossary_EN.md#term-shadow-mode). State
snapshot, RNG, batch, model revision, and exact implementation must match
across counterfactual branches.

## Admission sequence

1. positive `EQ-B1` and `EQ-B2`;
2. matched exact-candidate [profiling](glossary_EN.md#term-profiling);
3. `EX-IF0`;
4. policy-neutral trace collection;
5. separate `exact_verification` for `local_sweep(block_id)`;
6. `cost_feasibility`;
7. `zero_dangerous_misses`;
8. `net_efficiency`;
9. Pareto selection of `0–3` finalists;
10. predictor/controller preregistration;
11. shadow evaluation;
12. conditional active mode.

No later gate compensates for failure of an earlier safety gate.

## Shadow contract

Shadow output records the proposal, uncertainty, candidate block, expected
utility/regret, complete cost, and `fallback_exact` reason.
`controls_execution=false`; the actual trajectory remains canonical.

Hysteresis is preregistered separately as a stop threshold, wake threshold,
persistence, and emergency [fallback](glossary_EN.md#term-fallback). It does not replace the utility/regret
estimate.

## Active-mode condition

Active mode is permitted only after positive shadow evidence,
`zero_dangerous_misses`, and end-to-end cost benefit. If any condition fails,
the controller remains shadow-only.

`A-Max` is a conditional extension. The absence of an admissible active policy
does not invalidate `A-Core` and is an admissible negative result.

# Hierarchical QWake-PC design

[Русская версия](qwake-pc-design.md)

## Status and scope

This document describes future policy [architecture](glossary_EN.md#term-architecture) after `EX-IF0`. It is not a
controller preregistration, does not permit [execution](glossary_EN.md#term-execution), and does not modify B1
`isolated_layer_vjp`, B2 `composite_vjp`, or
`stage3b-b1-b2-prereg-v1`.

Until separate preregistration and positive shadow [evidence](glossary_EN.md#term-evidence),
`controls_execution=false`.

## Semantic boundary of the name

`QWake-PC` is a proper name rather than a conventional acronym. `Q` is
intentionally left without one expansion and denotes a bounded multidimensional
semantic marker:

- `Qualified` — an action is admissible only after registered gates;
- `Quotient` — the decision may use a task-relative
  [PC-TREF](glossary_EN.md#term-pc-tref) quotient representation;
- `Quality` — [endpoint](glossary_EN.md#term-endpoint) quality,
  [decision regret](glossary_EN.md#term-decision-regret), and dangerous misses
  constrain admissible actions;
- `Quiet` — low activity, cancellation, and temporal persistence provide
  diagnostic context but do not automatically permit stopping;
- `Quick` — reductions in sweeps, VJPs,
  [runtime](glossary_EN.md#term-runtime), or memory are separately tested
  engineering outcomes only.

These dimensions are not five sequential runtime conditions and need not all be
input features of every controller version. They bound the name's semantics;
adding further expansions of `Q` requires a separate terminology decision.

## Architectural role

`QWake-PC` occupies the control layer in the following hierarchy:

```text
PC-TREF   — theoretical framework for computational decision sufficiency
    ↓
PC-CATM   — mechanism model of correction formation, transport, and aggregation
    ↓
QWake-PC  — controller architecture and family for computation allocation
    ↓
QW-PC0 / QW-AB0 — versioned concrete-controller designs
```

[PC-TREF](glossary_EN.md#term-pc-tref) specifies which distinctions between
states must be preserved for an admissible action. [PC-CATM](glossary_EN.md#term-pc-catm)
explains the mechanisms that produce observed corrections and zero regimes.
`QWake-PC` operationalizes those foundations as control proposals or decisions,
but it is not one fixed algorithm.

In the current design space:

- `QW-PC0` denotes a conservative binary design: skip or run one full exact
  correction sweep;
- `QW-AB0` denotes the subsequent adaptive full-exact-sweep budget design.

These identifiers are design-level labels only. Every executable controller
requires its own contract, preregistration, shadow evaluation, and admission
decision. A negative result for one concrete controller does not invalidate
PC-CATM or PC-TREF.


## Multiscale extension and spike-like boundary

In the prospective
[multiscale mechanism–decision architecture](glossary_EN.md#term-multiscale-mechanism-decision-architecture),
a QWake policy may select the triple

```math
(scale, action, budget).
```

Norms, aggregation, admissible actions, regret, and cost remain separate at
every scale. Insufficient local diagnostics trigger
[adaptive escalation](glossary_EN.md#term-adaptive-escalation) toward a more
complete exact path.

The current [QWake-PC](glossary_EN.md#term-qwake-pc) may exhibit
[spike-like control dynamics](glossary_EN.md#term-spike-like-control-dynamics):
thresholded and sparse correction events, hysteresis, persistence, and a
discrete budget. The base states and errors remain non-spiking.

[`QWake-SPC`](glossary_EN.md#term-qwake-spc) is reserved for a possible PhD line
in which events become native spikes. It is not part of the current execution
plan and does not change the `A-Core` completion boundary.

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
- oracle-independent pre-action margin estimate, uncertainty, and first-order
  horizon from [`PC-TREF-SB`](pc-tref-sufficiency-boundary_EN.md);
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
4. policy-neutral trace and oracle-label collection;
5. passive boundary-estimator evaluation without pre-action leakage;
6. separate `exact_verification` for `local_sweep(block_id)`;
7. `cost_feasibility`;
8. `zero_dangerous_misses` with a preregistered upper confidence bound;
9. `net_efficiency`;
10. Pareto selection of `0–3` finalists;
11. predictor/controller preregistration;
12. shadow evaluation;
13. conditional active mode.

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

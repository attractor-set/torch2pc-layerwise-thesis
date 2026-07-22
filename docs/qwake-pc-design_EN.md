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


## Recursive multiscale semantics

The frozen direction uses one operator over a parent region `R` and a nested
aggregate family

```math
B_0=\varnothing\subset B_1\subset\cdots\subset B_K=R.
```

`QWake-PC` searches for the
[minimum sufficient compute aggregate](glossary_EN.md#term-minimum-sufficient-compute-aggregate)
rather than selecting an independent `GLOBAL` category. The previous design
labels retain the following compatibility interpretation:

```text
stop                      = B_0
local_sweep(block_id)     = 0 < B_k < R
full_exact                = B_K = R
fallback_exact            = exact current uncertified parent
```

Norms, thresholds, and cost remain scale-specific, while the exact-reference
relation, sufficiency margin, aggregate order, and fail-closed escalation use
one normative semantics. Local proposals do not compose automatically: the
parent validates joint sufficiency.

Temperature may only be an interpretable transform of a conservative
sufficiency-margin estimate.
[Spike-like control dynamics](glossary_EN.md#term-spike-like-control-dynamics)
is off the critical path and is admitted for measured chattering only when
basic hysteresis is insufficient. Base states and errors remain non-spiking;
[`QWake-SPC`](glossary_EN.md#term-qwake-spc) remains a future PhD line.

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
2. matched exact-[candidate](glossary_EN.md#term-candidate) [profiling](glossary_EN.md#term-profiling);
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

Shadow output records the proposal, uncertainty, [candidate](glossary_EN.md#term-candidate) block, expected
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

# Hierarchical QWake-PC design

[Русская версия](qwake-pc-design.md)

## Status and scope

This document specifies the general [QWake-PC](glossary_EN.md#term-qwake-pc)
[architecture](glossary_EN.md#term-architecture) and its only mandatory master's implementation,
[QWake-FP](glossary_EN.md#term-qwake-fp), after `EX-IF0`. It is not a
controller preregistration, does not permit
[execution](glossary_EN.md#term-execution), and does not modify B1
`isolated_layer_vjp`, B2 `composite_vjp`, or `stage3b-b1-b2-prereg-v1`.

`ADR-042` bounds QWake-FP experimental validation to the corrected Rosenbaum
FixedPred special case at `eta=1`. Until separate request freeze, [runtime](glossary_EN.md#term-runtime)
preflight, and authorization, `controls_execution=false`.

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

In the current mandatory design space:

- `QWake-FP` denotes one deterministic shadow implementation for a temporal
  FixedPred prefix, nested A0/A1/A2, a finite analytic registry, and a canonical
  suffix;
- `QW-PC0` and `QW-AB0` remain historical or future designs outside mandatory
  experimental validation.

QWake-PC generality is specified through interfaces and invariants. Only
QWake-FP is experimentally validated; its negative result does not invalidate
PC-CATM or PC-TREF, and its positive result does not establish transfer to
other algorithms or regimes.

## Recursive multiscale semantics

This semantics remains a future-work extension under `ADR-042` and is outside the mandatory QWake-FP image and confirmatory claim.

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

Active mode is permitted only after positive shadow [evidence](glossary_EN.md#term-evidence),
`zero_dangerous_misses`, and end-to-end cost benefit. If any condition fails,
the controller remains shadow-only.

`A-Max` is a conditional extension. The absence of an admissible active policy
does not invalidate `A-Core` and is an admissible negative result.

## Integrated frontier orchestration

[ADR-041](decisions/ADR-041-stage3b-integrated-frontier-corrective-semantics_EN.md)
limits future orchestration to ACCEPT_FRONTIER, ADVANCE_FRONTIER, and
COMPLETE_SUFFIX. ADVANCE_FRONTIER selects exactly one registered OBSERVATION,
ANALYTIC, or COMPUTE transition. [QWake-PC](glossary_EN.md#term-qwake-pc) does not define sufficiency or create
mechanism features: admission belongs to PC-TREF and evidence to PC-CATM. The
mandatory core is temporal FixedPred, and `controls_execution=false` remains in
force pending a separate decision.


## Bounded `QWake-FP` implementation and single image

[ADR-042](decisions/ADR-042-stage3b-qwake-fp-bounded-validation-and-single-image-gating_EN.md)
defines one immutable superset image and the campaign roles
`C1_COLLECTION / C2_CALIBRATION / C3_CONFIRMATORY / R_REPLICATION`.
Executable code is embedded in advance, but sensitive operations are activated
only through an internal [capability gate](glossary_EN.md#term-capability-gate)
at the effect boundary.

Policy is a frozen data manifest for the embedded interpreter. `SELECT_POLICY`
is permitted only in `C2_CALIBRATION`; confirmatory-partition access combined
with policy selection is forbidden. A next stage opens only through the sealed
receipt of its predecessor and matching image, source, and policy identities.

```text
qwake_fp_only_mandatory_implementation=true
execution_image_strategy=single_immutable_superset_image
stage_activation=fail_closed_permission_manifest
permission_checks_at_effect_boundaries=true
disabled_capability_executes=false
policy_representation=frozen_data_manifest
same_image_digest_required_across_c1_c2_c3_r=true
controls_execution=false
```

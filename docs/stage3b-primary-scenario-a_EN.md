# Stage 3B primary working Scenario A

[Русская версия](stage3b-primary-scenario-a.md)

## Decision

[Primary working Scenario](glossary_EN.md#term-primary-working-scenario) A is the
normative post-B0 plan. Its central question is:

> Which mechanisms create the cost of `Strict.state_inference`, and can full
> exact state-inference sweeps be reduced safely using local correction and
> [state-error transport](glossary_EN.md#term-state-transport) structure?

Scenario A keeps B0 immutable. New documents, controls, and candidates remain
separate from published B0 [evidence](glossary_EN.md#term-evidence).

## Current state as of 16 July 2026

A0–A8 are complete to the extent required for admission to the next stage: B0,
validity controls, `SI-MA0`, and corrective `SI-MA1` are published. Final
`SI-MA1` passed `CAL-COST-MA1` while retaining the negative `SI-MA0` result and
excluding future [control-plane cost](glossary_EN.md#term-control-plane-cost). The [theoretical foundation](pc-tref-pc-catm-theoretical-foundation_EN.md)
and [ADR-013](decisions/ADR-013-pc-tref-operational-semantics_EN.md) permit
B1/B2 preregistration. Implementation and [execution](glossary_EN.md#term-execution) remain closed until
[candidate](glossary_EN.md#term-candidate)-specific contracts exist.

## Theoretical linkage

- **PC-TREF** specifies which state distinctions are required for the next
  full exact-sweep decision;
- **PC-CATM** provides mechanism-aware aggregation and state-transport features;
- **exact verification** supplies the realized skipped-sweep utility;
- **[QWake-PC](glossary_EN.md#term-qwake-pc)** implements the policy only after shadow and safety gates.

Scenario A compares the nested $\phi_0,\ldots,\phi_5$ representations from
[PC-TREF Balanced Core](pc-tref-balanced-core_EN.md). The target is an empirical
cost-sufficiency frontier rather than proof of a globally minimal quotient.

## Required sequence

### A0 — design freeze

Freeze operator theory, terminology, hypotheses, stop rules, statistical unit,
test protection, and claim boundaries.

### A1 — unified research image

Build a separate Stage 3B image containing all observer and controller modes.
Before confirmatory campaigns, freeze the source commit, base image,
dependencies, and final image digest.

### A2 — shortcut controls

With observation fully disabled, compare:

1. `BP` versus iterative `FixedPred`, `eta=1`, `n=L`;
2. `BP` versus the reduced local shortcut;
3. iterative versus reduced shortcut.

Compare [endpoint](glossary_EN.md#term-endpoint) parameter gradients and one optimizer step. The shortcut does
not replace B0 or become a new [baseline](glossary_EN.md#term-baseline).

### A3 — observer non-interference and overhead

First verify semantic agreement across:

```text
no_hooks
instrumented_disabled
counters_only
tensor_summaries
full_attribution
```

Then measure framework branching, counters, reductions, synchronization,
host transfer, and serialization separately.

### A4 — deterministic correction controls

Required cases are exact NCZ, exact and near ECZ, aligned channels, orthogonal
non-cancellation, three-channel ECZ, channel-refinement invariance, and
zero-safe comparison.

### A5 — deterministic transport controls

Test identity, scaled, null, and orthogonal operators and a direct cumulative
reverse probe. Low observed contribution with an active source and attenuated
transport is not intrinsic NCZ.

### A6 — Rosenbaum temporal control

Use `eta=1`, `n=L` as a wavefront control for error arrival, required and
redundant sweeps, and correct layer, sweep, and state-version indexing.

### A7 — block probe in shadow mode

Compare isolated, composite, and chunked-composite vector–Jacobian products on
one frozen snapshot. The probe does not control [execution](glossary_EN.md#term-execution) or replace `Strict`
before the B2 gate.

### A8 — SI-MA0 mechanism attribution

Partition `state_inference` into:

```text
inference_setup
lower_prediction_and_error
upper_state_vjp
component_aggregation
belief_update
sweep_bookkeeping
inference_finalize
```

Store state and Jacobian versions, channels, transport diagnostics, VJP counts,
[saved tensors](glossary_EN.md#term-saved-tensors), graph lifetime, synchronization, and observed corrections.

The primary gate is:

\[
u_l^{(\mathrm{reconstructed})}\approx u_l^{(\mathrm{observed})}.
\]

Real NCZ/ECZ observations are not interpreted before this gate passes.

### A9 — B1/B2

Separate B1/B2 preregistration is frozen by `STAGE3B-B1*`, `STAGE3B-B2*`,
the [overview](stage3b-b1-b2-preregistration_EN.md), and
[ADR-014](decisions/ADR-014-stage3b-b1-b2-candidate-contracts_EN.md).

- B1: `isolated_layer_vjp`;
- B2: only `composite_vjp`; a block/chunk variant requires a new protocol.

After the publication tag, B1 is implemented. B2 remains closed until sealed
`EQ-B1`; [matched profiling](glossary_EN.md#term-matched-profiling) remains closed until `EQ-B1` and `EQ-B2`.

### A10 — `EX-IF0`

The [exact-implementation freeze](glossary_EN.md#term-exact-implementation-freeze)
selects canonical `Strict`, B1, or B2 before predictor-label and counterfactual-
evidence generation.

### A11 — passive diagnostics

Record `NCZ[intrinsic]`, `NCZ[state_transport_masked]`, `NCZ[unresolved]`,
`ECZ`, `active_non_ecz`, `activity_guard`, and `invalid`. Analyze frequencies,
layer/sweep structure, transitions, and association with next exact-sweep
utility. Diagnostics cannot control execution before `EX-IF0`.

#### A11-OFF0 — policy-neutral counterfactual traces

After `EX-IF0` and before predictor training, one restored snapshot is branched
into the labels frozen by the B1/B2 contracts:

```text
stop
native_one
exact_one
```

Each branch records $\phi_0,\ldots,\phi_k$, temporal history, and endpoint
utility/regret. Exact reference creates oracle skip regret, oracle margin $M^*$,
and the one-step boundary sign; pre-action features remain separate. Each
branch also records feature costs, transitions, [fallback](glossary_EN.md#term-fallback)
reasons, and complete provenance. Branches are offline labels and
`controls_execution=false`. The independent unit is `model_seed`; the test
split remains closed.

A separate post-`EX-IF0` preregistration may add `local_sweep(block_id)`.
That branch is outside B1/B2 and does not modify
`stage3b-b1-b2-prereg-v1`.

#### A11-OFF1 — sequential offline screening

On the development split, policy families pass:

1. `cost_feasibility`;
2. `safety` with `zero_dangerous_misses`;
3. `net_efficiency` over the complete [cost vector](glossary_EN.md#term-cost-vector);
4. Pareto screening.

Screening returns `0–3` finalists. Retaining exactly three variants is not
required; `0` is an admissible negative result.

### A12 — local predictor and controller preregistration

The [local predictor](glossary_EN.md#term-local-predictor) is preregistered only
after `A11-OFF1`, uses frozen features and `model_seed` splits, and does not
modify beliefs. Its boundary branch estimates $\widehat M_b$ and uncertainty
against oracle $M^*$ under
[`PC-TREF-SB`](pc-tref-sufficiency-boundary_EN.md); the first-order horizon
remains a separate ablation. A separate controller contract freezes action labels,
representation, thresholds, hysteresis, fallback, and control-plane cost before
shadow evaluation.

### A13 — exact verification of ECZ-targeted local sweep

[Counterfactual exact verification](glossary_EN.md#term-exact-verification)
creates proposed local and full exact branches from identical state. `ECZ` may
select only a candidate block. It does not establish that
`local_sweep(block_id)` is safe, cheaper, or sufficient.

The primary target is
[endpoint-gradient utility](glossary_EN.md#term-endpoint-gradient-utility); a
[dangerous miss](glossary_EN.md#term-dangerous-miss) is the safety barrier.
The local action cannot enter a policy family before `exact_verification`
passes.

### A14 — hierarchical `QWake-PC` shadow mode

After separate preregistration, `QWake-PC` emits proposals in the hierarchy:

```text
stop
→ ECZ-targeted local sweep
→ full exact sweep
→ fallback_exact
```

`controls_execution=false`. hysteresis is a policy guard rather than a
substitute for utility/regret. The contract freezes stop/wake thresholds,
persistence, and emergency `fallback_exact`.

### A15 — conditional active mode and `A-Max`

Only after positive shadow evidence, `zero_dangerous_misses`, and the
end-to-end cost gate may the controller manage execution. Observer and
control-plane costs are measured separately; the test split is not used for
selection.

`A-Max` is not an automatic continuation: it opens only after a successful
shadow result. Otherwise the study retains `A-Core`, negative policy findings,
and the applicability boundary.

Normative documents:
[QWake-PC design](qwake-pc-design_EN.md),
[ECZ-targeted local sweep](ecz-targeted-local-sweep_EN.md), and
[future-policy boundary](stage3b-future-policy-boundary_EN.md).

## Completion levels

### A-Min

A0–A8 and passive PC-CATM diagnostics and PC-TREF ablation are complete. This is a standalone
mechanism-and-measurement study.

### A-Core

B1/B2, EX-IF0, the predictor, exact verification, and shadow QWake-PC are also
complete.

### A-Max

Active QWake-PC reduces [device time](glossary_EN.md#term-device-time) while preserving registered endpoint-gradient
and safety bounds.

Failure to reach A-Max does not invalidate A-Min or A-Core.

## Statistical contract

The independent unit is an independently trained model identified by
`model_seed`. Layer, sweep, batch, sample, and technical repetition are nested
observations. Features, thresholds, and policies are selected without [test-dataset access](glossary_EN.md#term-test-dataset-access).

## Stop rules

- shortcut failure blocks shortcut interpretation;
- observer perturbation blocks attribution;
- reconstruction failure blocks real NCZ/ECZ interpretation;
- composite/isolated disagreement blocks B2;
- insufficient transport evidence forbids `sleep_candidate`;
- absent incremental ECZ value leaves ECZ descriptive;
- failed cross-model generalization leaves QWake-PC shadow-only;
- excessive dangerous misses block active mode;
- sweep reduction without [runtime](glossary_EN.md#term-runtime) reduction is reported as a negative
  engineering result.

## Limited extension

PNZ and the parameter tangent operator are included only as theory, a
deterministic control, and an optional small passive audit.

## Outside mandatory scope

- active kernel preconditioning;
- dual Gauss–Newton [predictive coding](glossary_EN.md#term-predictive-coding);
- full parameter-spectrum analysis;
- layer-level skipping inside a sweep;
- plasticity control;
- continual learning;
- low-rank kernel training.

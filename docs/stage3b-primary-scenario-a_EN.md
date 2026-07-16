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

The next stage is **separate preregistration**, not immediate [profiling](glossary_EN.md#term-profiling):

- B1: `isolated_layer_vjp`;
- B2: `composite_vjp` or a prespecified block-composite variant.

Each contract freezes reference path, state/belief/RNG restoration, numerical-
equivalence endpoints and tolerances, [decision regret](glossary_EN.md#term-decision-regret),
norm contracts, the [cost vector](glossary_EN.md#term-cost-vector), observer/
control-plane separation, [fallback](glossary_EN.md#term-fallback), independent unit, and stop rules. Only a
candidate that passes deterministic controls, ROCm smoke, and a separate
numerical-equivalence/safety gate may enter matched confirmatory profiling.

### A10 — EX-IF0

The [exact-implementation freeze](glossary_EN.md#term-exact-implementation-freeze)
selects canonical `Strict`, B1, B2, or chunked B2 before predictor-label and
counterfactual-evidence generation.

### A11 — passive diagnostics

Record:

```text
NCZ[intrinsic]
NCZ[state_transport_masked]
NCZ[unresolved]
ECZ
active_non_ecz
activity_guard
invalid
```

Analyze frequencies, layer and sweep structure, transitions, persistence across
models, and association with next exact-sweep utility.

### A12 — local predictor

The [local predictor](glossary_EN.md#term-local-predictor) remains in shadow
mode and uses preregistered geometry, transport, layer/sweep, residual-history,
and uncertainty features. Splits are grouped by `model_seed`.

### A13 — exact verification

[Counterfactual exact verification](glossary_EN.md#term-exact-verification)
creates proposed and exact branches from identical state. The primary target is
[endpoint-gradient utility](glossary_EN.md#term-endpoint-gradient-utility). A
[dangerous miss](glossary_EN.md#term-dangerous-miss) is the primary safety gate.

### A14 — QWake-PC shadow

[QWake-PC](glossary_EN.md#term-qwake-pc) emits only proposals:

```text
continue_exact
sleep_candidate
wake_candidate
stop_candidate
fallback_exact
```

`controls_execution=false`.

### A15 — active full-sweep allocation

After the shadow gate, the controller may manage only full exact sweeps.
Compare frozen exact execution, a fixed budget, C1, C2, predictor-only,
regime-only, QWake-PC, and a post-hoc oracle upper bound.

Primary outcomes are endpoint-gradient preservation, exact sweeps and VJPs,
device and wall time, memory and saved tensors, dangerous misses, [fallback](glossary_EN.md#term-fallback)
frequency, and stability across `model_seed`.

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

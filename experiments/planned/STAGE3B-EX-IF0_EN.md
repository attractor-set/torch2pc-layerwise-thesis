# Stage 3B `EX-IF0`: exact implementation and oracle sweep-boundary freeze

[Русская версия](STAGE3B-EX-IF0.md)

Status: **design contract frozen; execution and label generation closed**.

## 1. Purpose

`EX-IF0` freezes the [exact implementation](../../docs/glossary_EN.md#term-exact-implementation-freeze) used by subsequent offline branches to compute task-relative regret, the [oracle sufficiency margin](../../docs/glossary_EN.md#term-oracle-sufficiency-margin), and the minimum stably sufficient sweep index.

The machine-readable source of truth is:

```text
experiments/frozen/stage3b-ex-if0-design-v1/contract.json
```

This freeze does not execute new computation, generate oracle labels, collect features, or activate control.

## 2. Exact implementation selection

The published matched analysis retained both new exact candidates — `isolated_layer_vjp` and `composite_vjp` — as `reject_or_revise` for both `FixedPred` and `Strict`. Neither B1 nor B2 therefore replaces the mandatory fallback path.

`EX-IF0 v1` selects:

```text
selected_candidate_id=stage2_baseline
selected_role=canonical_exact_reference_and_fail_closed_fallback
selected_methods=fixedpred,strict
selection_is_superiority_claim=false
```

Selecting B0 preserves the already validated exact path; it is not a universal superiority claim. B1/B2 remain published numerically admissible studied candidates with their recorded `reject_or_revise` engineering decisions.

## 3. Full reference trajectory

For every registered configuration, the reference sweep count

\[
K_{\mathrm{ref}}
\]

equals the frozen `inference_steps` of that method and configuration. Adaptive early stopping of the reference trajectory is forbidden.

State

\[
S_t
\]

is defined after sweep `t` completes, with `S_0` denoting the initialized state before the first sweep. A potential stop decision is located after `S_t` is complete and before sweep `t+1` begins.

## 4. Task-relative endpoint

For each `S_t`, endpoint readout

\[
Y_t=\Gamma(S_t)
\]

contains:

- named parameter-gradient tensors;
- endpoint beliefs at registered layers;
- endpoint loss;
- mandatory shape, finite-value, and provenance guards.

The exact endpoint is

\[
Y_{\mathrm{ref}}=\Gamma(S_{K_{\mathrm{ref}}}).
\]

A shorter prefix need not match the full intermediate trajectory. Sufficiency in this contract is relative to the required endpoint response.

## 5. Regret and signed margin

The existing B1/B2 `rocm_float32` thresholds are frozen:

```text
max_abs=1e-5
max_relative_l2=1e-3
min_cosine=0.999
zero_atol=1e-7
```

The maximum normalized violation across every registered component is used without averaging:

\[
r_\Gamma(t)=\max\left(
\frac{E_{\mathrm{abs}}(t)}{\tau_{\mathrm{abs}}},
\frac{E_{\mathrm{rel}}(t)}{\tau_{\mathrm{rel}}},
\frac{1-C(t)}{1-\tau_{\cos}}
\right).
\]

Structural mismatch, non-finite values, or component mismatch imply

\[
r_\Gamma(t)=+\infty.
\]

The signed margin is

\[
M^*(t)=1-r_\Gamma(t).
\]

Sweep `t` is sufficient if and only if

\[
M^*(t)\geq0.
\]

Cost cannot compensate for a negative margin.

## 6. Minimum stably sufficient sweep

The first isolated threshold pass is not sufficient. Full suffix stability is required:

\[
t^*=\min\left\{t:\;M^*(j)\geq0\quad\forall j\in[t,K_{\mathrm{ref}}]\right\}.
\]

`S_K_ref` must pass an identity self-check. If the exact endpoint fails its own check, the dataset fails closed.

A future oracle table must retain:

```text
sufficient_at_t
exact_reference_regret
oracle_sufficiency_margin_M_star
minimum_stably_sufficient_sweep_t_star
remaining_unnecessary_sweeps
```

This document does not create that table.

## 7. Counterfactual branches

The schema retains labels:

```text
stop
native_one
exact_one
```

They are post-action offline-dataset records, not controller actions. Under `EX-IF0 v1`, both `native_one` and `exact_one` use the selected `stage2_baseline`; identity equivalence is therefore expected. One physical execution may back both logical labels only when provenance records the alias and endpoint fingerprints agree.

Branching one snapshot requires restoration of parameters, optimizer, beliefs, batch, RNG, and method configuration.

## 8. Feature/label boundary

A pre-action representation for the decision after `S_t` may use only information materialized no later than `S_t`.

Features may not include:

- future states `S_{t+1},...,S_K_ref`;
- `Y_ref`;
- `M^*(t)`;
- `t^*`;
- counterfactual branch outcomes.

Those quantities are post-action oracle labels. Collection of `A0/A1/A2`, estimator training, and a shadow cascade require later separate contracts.

## 9. Aggregate hierarchy

The temporal family is already defined by prefixes of the full reference trajectory:

\[
P_0\subset P_1\subset\cdots\subset P_{K_{\mathrm{ref}}}.
\]

Only the normative spatial form is frozen here:

\[
B_0=\varnothing\subset B_1\subset\cdots\subset B_K=R.
\]

At least two scales are mandatory:

1. layers within a registered block;
2. blocks within the network.

Concrete spatial memberships must be frozen separately before `A11-OFF0` label generation. Power-set enumeration is forbidden; only preregistered nested prefixes are admissible. No separate `GLOBAL` action is introduced, and a full root sweep remains the maximum aggregate.

## 10. Failure and safety

A future [dangerous miss](../../docs/glossary_EN.md#term-dangerous-miss) is a `stop` proposal when `M^*(t)<0`. Future confirmatory admission permits zero such observations. Continuing when a sweep is already sufficient is quality-safe but is charged as computational inefficiency.

No estimator exists before separate preregistration, so it cannot yet abstain. Full `stage2_baseline` remains the [fallback](../../docs/glossary_EN.md#term-fallback).

## 11. Frozen boundary

```text
ex_if0_opened=true
ex_if0_complete=true
ex_if0_protocol_frozen=true
exact_implementation_frozen=true
exact_implementation_candidate=stage2_baseline
minimum_sufficient_sweep_rule_frozen=true
ex_if0_execution_permitted=false
oracle_label_generation_open=false
feature_collection_permitted=false
recursive_aggregate_execution_open=false
a11_off0_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

The next admissible transition is a separate preregistration of the concrete hierarchy, snapshot branching, and oracle trace generation for `A11-OFF0`. No execution opens automatically.

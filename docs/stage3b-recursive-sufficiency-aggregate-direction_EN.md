# Stage 3B recursive sufficient-aggregate direction freeze

[Русская версия](stage3b-recursive-sufficiency-aggregate-direction.md)

## 1. Status and boundary

This document freezes the primary research direction after a separate
publication gate for the sealed B1/B2 analysis. It is a design-only decision:
it does not authorize [execution](glossary_EN.md#term-execution), open `EX-IF0`, create labels, train a
predictor, activate `QWake-PC`, or modify sealed B1/B2 [evidence](glossary_EN.md#term-evidence).

> **Historical boundary:** Section 12 preserves the state at ADR-035, when
> `EX-IF0` was still pending. Current post-freeze state is defined by
> `STATUS_EN.md` and `experiments/frozen/stage3b-ex-if0-design-v1/contract.json`;
> the historical markers below are not the current admission state.

Until a separate preregistration, the following remain in force:

```text
controls_execution=false
policy_activation_permitted=false
test_dataset_access=false
```

## 2. Central research question

> Can one recursive mechanism use an estimate of the margin to a task-relative
> sufficiency boundary to select minimum sufficient compute aggregates across
> multiple scales of predictive-coding inference under bounded exact-reference
> regret?

The first empirical object is not a complete controller. It is the existence
and state dependence of minimum sufficient aggregates.

## 3. Basis in B1/B2 results

B1 `isolated_layer_vjp` and B2 `composite_vjp` passed their registered numerical
equivalence gates, while matched analysis preserved different cost vectors and
`reject_or_revise` decisions. The supported bounded conclusion is therefore:

```math
a\sim_N b\;\not\Rightarrow\;\mathbf C(a)=\mathbf C(b).
```

Cost is not invariant within the studied class of numerically equivalent
procedures. This result establishes a nontrivial resource-choice premise, but
it does not prove:

- existence of a cheaper partial sweep;
- necessity of an adaptive policy;
- predictability of a sufficient aggregate;
- end-to-end `QWake-PC` benefit.

## 4. Recursive compute aggregate

Let `R` be a parent compute region and let

```math
\mathcal B_R=\{B_0,B_1,\ldots,B_K\}
```

be a preregistered nested family of admissible aggregates:

```math
B_0=\varnothing\subset B_1\subset\cdots\subset B_K=R.
```

The same semantics applies at every registered scale:

- `B_0=∅` skips the parent computation;
- `∅⊂B_k⊂R` executes a partial aggregate;
- `B_K=R` executes the parent's full exact aggregate.

No separate `GLOBAL` policy action is introduced. A full root sweep emerges as
the maximum aggregate. `fallback_exact` executes the full exact computation of
the minimum uncertified parent and coincides with a full exact sweep at the
root.

## 5. Sufficiency and oracle decision

For state `x`, parent `R`, and [candidate](glossary_EN.md#term-candidate) `B`, define task-relative
exact-reference regret:

```math
r_\Gamma(x,B)=D_\Gamma(Y(x,B),Y(x,R)).
```

The [oracle sufficiency margin](glossary_EN.md#term-oracle-sufficiency-margin) is

```math
M_R^*(B;x)=\delta_R-r_\Gamma(x,B).
```

An aggregate is sufficient when `M_R^*(B;x)≥0`. The
[minimum sufficient compute aggregate](glossary_EN.md#term-minimum-sufficient-compute-aggregate)
is selected only among sufficient candidates:

```math
B_R^*(x)=\arg\min_{B\in\mathcal B_R:\,M_R^*(B;x)\geq0}\mathbf C_R(B),
```

with a preregistered Pareto rule and deterministic tie-break when the cost
vector is only partially ordered.

`M_R^*` is a post-action oracle label. An active mechanism may use only a
separately validated pre-action estimate and its conservative bound.

## 6. Minimum validation scales

The first confirmatory core is limited to two spatial scales:

1. layers within a preregistered block;
2. blocks within the network.

Both scales retain the same:

- exact-reference relation;
- sufficiency-margin definition;
- aggregate inclusion order;
- safety contract;
- `fallback_exact` semantics;
- cost rule and tie-break.

Shared semantics does not imply shared numerical thresholds, norms, or costs.
Cross-scale transfer requires a separate gate.

## 7. Required existence gates

### `E2` — opportunity existence

```math
\exists x,B\subset R:\quad
M_R^*(B;x)\geq0\;\land\;\mathbf C_R(B)\prec_C\mathbf C_R(R).
```

Failure of `E2` closes the partial-aggregate branch at the tested scale.

### `E3` — state dependence

```math
\exists x_1,x_2:\quad B_R^*(x_1)\neq B_R^*(x_2).
```

Failure of `E3` means that an adaptive controller is not justified and a static
alternative must be considered.

### `E5` — cross-scale semantic reuse

The same normative contract must apply at both scales without changing the
meaning of sufficiency, exact reference, or fail-closed escalation. Failure
forbids a scale-invariance claim.

### `H0` — boundary occupancy

The study measures states with `|M_R^*|≤ε_M`. Sparse occupancy near the boundary
may make temperature or hysteresis unnecessary.

### `P0` — diagnostic opportunity

The study tests whether cheap pre-action features are associated with the sign
of `M_R^*`. `P0` is not predictor admission.

## 8. Temperature and spike-like dynamics

Compute temperature is permitted only as an interpretable transform of the
conservative margin estimate:

```math
T_R(B;x)=\sigma\!\left(-\underline M_R(B;x)/s_R\right).
```

It does not replace the margin and is not an independently trained target.

[Spike-like control dynamics](glossary_EN.md#term-spike-like-control-dynamics)
is not on the critical path. Its admissible role is suppression of measured
chattering near a sufficiency boundary. The priority order is:

```text
RAW threshold
→ hysteresis if chattering is observed
→ accumulator/reset/refractory only if hysteresis is insufficient
```

Fully spike-native dynamics remains outside the master's thesis boundary.

## 9. Evidence sequence

```text
B1/B2 publication gate
→ bounded cost-noninvariance interpretation
→ EX-IF0 and B0 exact-reference freeze
→ aggregate hierarchy and oracle protocol freeze
→ counterfactual snapshot branches
→ E2 existence
→ E3 state dependence
→ E5 cross-scale semantics
→ P0 diagnostic opportunity
→ pre-action estimator
→ shadow QWake-PC
→ conditional active control
```

No late result compensates for an earlier safety-gate failure. Every negative
result is admissible and preserved.

## 10. Excluded directions

Before `E2/E3/E5/P0` decisions, the critical path excludes:

- B3 and new VJP implementations;
- compiler optimization;
- stochastic simulated annealing;
- online reinforcement learning;
- contextual bandits;
- active sequential policy;
- exhaustive enumeration of `2^{|R|}` aggregates;
- a spike-like accumulator without measured chattering.

## 11. Claim boundary

Before `E2`, no claim may state that a partial aggregate is cheaper and
sufficient. Before `E3`, no claim may state that adaptive control is necessary.
Before `E5`, no claim may state scale invariance. Before shadow
`net_efficiency`, no claim may state end-to-end cost reduction.

## 12. Frozen status

```text
RESEARCH_DIRECTION_FROZEN=true
CENTRAL_OBJECT=minimum_task_sufficient_compute_aggregate
CONTROL_SEMANTICS=recursive_multiscale
GLOBAL_POLICY_ACTION=false
FULL_SWEEP=maximum_root_aggregate
EXACT_REFERENCE=B0_pending_EX_IF0
TEMPERATURE=conservative_margin_transform
HYSTERESIS=conditional_on_observed_chattering
SPIKE_ACCUMULATOR=conditional
CONTROLLER_IMPLEMENTATION_AUTHORIZED=false
POLICY_ACTIVATION_PERMITTED=false
NEXT_FORMAL_TRANSITION=publication_gate_then_EX_IF0
```

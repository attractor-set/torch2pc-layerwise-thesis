# ADR-050: `QW-LC0` semantics-and-scope freeze

[Russian version](ADR-050-stage3b-qwake-lc0-semantics-scope-freeze.md)

- **Status:** accepted as `QW-LC0`; [execution](../glossary_EN.md#term-execution) remains closed
- **Date:** 25 July 2026

## Context

The PR 111 post-merge transition opened only the `QW-LC0` documentation freeze.
The [baseline](../glossary_EN.md#term-baseline) [evidence](../glossary_EN.md#term-evidence) is already sealed, but it
contains no `LOCAL_COMPUTE` implementation or validation.

Earlier decisions define the temporal frontier, the `FixedPred` `eta=1` special
case, the complete canonical suffix, and closed permissions. This slice removes
the remaining ambiguity among the result, its production path, the resource
path, and cost without assigning unobserved properties to a
[candidate](../glossary_EN.md#term-candidate).

## Decision

### 1. Four independent objects

For action `a` from state `s`, distinguish normatively:

1. the [required result](../glossary_EN.md#term-required-result) `R(a,s)`, the
   registered task-relative response;
2. the [computational mechanism](../glossary_EN.md#term-computational-mechanism)
   `M(a)`, the registered algorithmic path;
3. the [resource trajectory](../glossary_EN.md#term-resource-trajectory)
   `Γ(a,s)`, ordered measured resource events from action start through the
   result or reserve path;
4. the [cost vector](../glossary_EN.md#term-cost-vector)
   `C(a,s)=Φ(Γ(a,s))`, the decision-facing representation of the measured
   resource trajectory.

Equality in `R` determines neither equality in `M`, `Γ`, nor `C`. `QW-LC1`
freezes response serialization and [response equivalence](../glossary_EN.md#term-response-equivalence).
`QW-LC2` freezes the measurement
schema for `Γ`, the map `Φ`, and [cost equivalence](../glossary_EN.md#term-cost-equivalence).

### 2. Action family

`LOCAL_COMPUTE` contains exactly:

```text
LOCAL_SWEEP
ANALYTIC_COMPLETION
```

`LOCAL_SWEEP` denotes an explicit registered local update over a bounded
aggregate. `ANALYTIC_COMPLETION` denotes registered analytic production of the
required result without explicitly replaying the complete local-update
sequence.

Capability presence is not permission. Neither member may directly authorize
`ACCEPT_FRONTIER`; the complete `COMPLETE_SUFFIX` remains the mandatory exact
[fallback](../glossary_EN.md#term-fallback).

### 3. Single first candidate

The first [candidate](../glossary_EN.md#term-candidate) is
`fixedpred_eta1_wavefront_completion_v1`, simultaneously bounded to:

```text
algorithm=FixedPred
eta=1
architecture=lenet_classic
executor=stage2_baseline
mode=shadow_post_action_validation
```

Response equivalence, safety, coverage, and cost are not yet established. The
candidate does not generalize to `Strict`, other `eta`, other
[architectures](../glossary_EN.md#term-architecture), arbitrary graphs, skip
connections, a universal symbolic solver, full-trajectory reconstruction, or
active control.

### 4. Claim boundary

`QW-LC0` establishes only:

- separation of `R/M/Γ/C`;
- the finite `LOCAL_COMPUTE` membership;
- the bounded first-candidate scope;
- the sequence of later freezes.

It establishes no response equivalence, cost superiority, implementation
correctness, policy admissibility, transferability, deployment readiness, or
scientific result.

### 5. Deferred freezes

```text
QW-LC1 = response schema, mandatory observables, ~R
QW-LC2 = measured Gamma, Phi mapping, ~C
QW-LC3 = matched shadow validation and exact reserve
QW-LC4-I = bounded implementation
QW-LC4-F = extension image and single-attempt authorization
QW-LC4-E = sealed engineering validation
```

## Machine-readable freeze

The contract is sealed as:

```text
experiments/frozen/stage3b-qwake-lc0-semantics-scope-v1/contract.json
experiments/frozen/stage3b-qwake-lc0-semantics-scope-v1/SHA256SUMS
```

## Execution boundary

```text
qwake_qw_lc0_semantics_scope_frozen=true
qwake_qw_lc0_contract_id=stage3b-qwake-lc0-semantics-scope-v1
qwake_qw_lc1_transition_permitted=false
qwake_qw_lc1_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC0-repository-freeze
qwake_post_merge_next_slice=QW-LC1
```

This slice does not invoke the model, read tensors, or create post-action oracle
labels. Later negative findings are retained without changing criteria.

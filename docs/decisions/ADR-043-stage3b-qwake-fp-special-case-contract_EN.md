# ADR-043: QWake-FP special-case contract freeze

[Russian version](ADR-043-stage3b-qwake-fp-special-case-contract.md)

- **Status:** accepted as `QW-2`; [execution](../glossary_EN.md#term-execution) remains closed
- **Date:** 2026-07-24

## Context

ADR-042 limited mandatory validation to one `QWake-FP` implementation, while
`QW-1` implemented the pure state, action, permission, and receipt core. Before
building the superset pipeline, that general core must be bound unambiguously to
one finite [configuration](../glossary_EN.md#term-configuration). Otherwise implementation could change the method,
horizon, response, features, analytics, costs, or baselines after seeing early
trajectories.

## Decision

### 1. Single mandatory special case

Only the following configuration is frozen:

```text
method=fixedpred
eta=1
canonical_executor=stage2_baseline
architecture=lenet_classic
horizon_rule=registered_inference_steps
qwake_fp_generalization_claim=false
```

`Strict`, arbitrary `eta`, another [architecture](../glossary_EN.md#term-architecture), and a learned online controller
are outside the mandatory QW-2 contract.

### 2. Decision epoch and canonical suffix

Snapshot `S_t` is materialized after sweep `t` and before sweep `t+1`, including
`S_0` before the first sweep. The finite horizon is the registered
`inference_steps` of the concrete configuration:

```text
decision_epoch=after_S_t_before_sweep_t_plus_1
candidate_indices=t_in_[0,K_ref]
snapshot_zero=initialized_state_before_first_sweep
canonical_suffix=remaining_stage2_baseline_sweeps
```

`COMPLETE_SUFFIX` always completes the remaining `stage2_baseline` and remains
the fail-closed [fallback](../glossary_EN.md#term-fallback).

### 3. Required response and primary defect

The task-relative response contains exactly:

```text
named_parameter_gradients
endpoint_beliefs
endpoint_loss
```

The primary defect is inherited from `EX-IF0`:

```text
r_Gamma(t)=max(
  max_abs/max_abs_limit,
  relative_l2/max_relative_l2_limit,
  (1-cosine)/(1-min_cosine)
)
structural_or_finite_failure=infinity
M_star(t)=1-r_Gamma(t)
sufficient(t)=M_star(t)>=0
```

The tolerance profile is immutable:

```text
lane=rocm_float32
max_abs=1e-5
max_relative_l2=1e-3
min_cosine=0.999
zero_atol=1e-7
```

The minimum sufficient prefix uses full-suffix stability only:

```text
t_star=min{t: sufficient(j)=true for every j in [t,K_ref]}
```

### 4. Finite observation axis

The deployable axis has exactly three cumulative levels.

#### `A0`

Structural fields only, with no tensor-value reads:

```text
snapshot_id
compute_step
reference_horizon_k_ref
remaining_sweeps
registered_layer_order
registered_block_order
acquired_analytic_ids
diagnostic_budget_remaining_ns
```

#### `A1`

`A0` plus a finite set of cheap device-side reductions:

```text
global_prediction_error_l2_sq
global_state_delta_l2_sq
per_layer_prediction_error_l2_sq
per_layer_state_delta_l2_sq
per_layer_prediction_error_max_abs
per_layer_state_delta_max_abs
```

#### `A2`

`A1` plus local reductions over deterministic nested prefixes of size `32`,
`128`, and `256`. A tensor smaller than the prefix uses the whole tensor. Indices
are selected without replacement by hash ranking over:

```text
contract_id, model_seed, batch_id, layer_id, tensor_role
```

`L2^2` and `max_abs` are stored for `prediction_error`, `state_delta`, and
`belief`.

`O`, `t_star`, the future reference trajectory, and `M_star` never enter a
pre-action observation level.

### 5. Finite analytic registry

Exactly three registered analytics are permitted:

```text
rosenbaum_wavefront_status_v1   exact         minimum=A0
residual_persistence_v1         heuristic     minimum=A1
cost_dominance_v1               conservative  minimum=A0
```

- `rosenbaum_wavefront_status_v1` is the analytic positive control for the known
  component-completion order;
- `residual_persistence_v1` is diagnostic and a [baseline](../glossary_EN.md#term-baseline) only;
- `cost_dominance_v1` may prune a dominated acquisition but cannot establish
  sufficiency.

No analytic may execute `ACCEPT_FRONTIER` directly. A positive decision requires
the frozen risk admission selected offline in C2.

### 6. Baselines

The closed baseline registry is:

```text
B0 full canonical suffix
B1 fixed prefix
B2 registered prediction-error/residual threshold
B3 A0-only
B4 fixed A0->A1->A2 cascade
B5 fixed analytic registry
B6 frozen QWake-FP
B7 post-action oracle frontier
```

`B7` is an offline non-deployable upper bound only.

### 7. Three matched observer pairs

Pre-freeze validation contains exactly:

```text
P0: B0 <-> B0+A0
P1: B0 <-> B0+A0+A1
P2: B0 <-> B0+A0+A1+A2
```

Within every pair, [endpoint](../glossary_EN.md#term-endpoint) response, parameter gradients, beliefs, loss,
transition sequence, final RNG state, and snapshot identity must match. Observer
host/[device time](../glossary_EN.md#term-device-time), synchronization, D2H, temporary memory, and trace bytes are
measured separately.

### 8. Cost mapping

Raw edge measurement stores:

```text
host_time_ns
device_time_ns
synchronization_count
d2h_bytes
temporary_memory_bytes
trace_bytes
```

Each time edge belongs to exactly one category:

```text
compute_ns
observer_ns
diagnostic_ns
control_ns
fallback_ns
```

The primary basis is calibrated host critical-path allocation. [Device time](../glossary_EN.md#term-device-time) is
published independently and is not added a second time. Memory is the maximum
temporary memory on the replayed path; D2H and trace remain explicit vector
components. Selection order is:

```text
safety -> coverage -> cost
```

### 9. Roles and receipts

QW-2 creates no new permission matrix. It inherits the closed allowlists and
receipt requirements from QW-1 byte-for-byte. In particular, C2 remains strictly
offline and receives no `EXECUTE_FIXEDPRED`, observation collection, new oracle,
or confirmatory access.

### 10. Machine-readable freeze

The canonical contract is produced by the pure module:

```text
src/torch2pc_thesis/stage3b_qwake_fp_spec.py
```

and sealed as:

```text
experiments/frozen/stage3b-qwake-fp-special-case-v1/contract.json
experiments/frozen/stage3b-qwake-fp-special-case-v1/SHA256SUMS
```

A regression test requires exact agreement among canonical JSON, its SHA-256,
and the Python specification.

## Execution boundary

This ADR does not permit FixedPred execution, A0/A1/A2 collection, live
analytics, oracle-label generation, policy activation, or [test-[dataset](../glossary_EN.md#term-dataset) access](../glossary_EN.md#term-test-dataset-access).

```text
qwake_fp_special_case_contract_frozen=true
qwake_fp_special_case_contract_id=stage3b-qwake-fp-special-case-v1
qwake_fp_method=fixedpred
qwake_fp_eta=1
qwake_fp_canonical_executor=stage2_baseline
qwake_fp_architecture=lenet_classic
qwake_fp_horizon_rule=registered_inference_steps
qwake_fp_primary_defect=ex_if0_r_Gamma_full_suffix_stability
qwake_fp_observation_registry=A0,A1,A2
qwake_fp_analytic_registry=rosenbaum_wavefront_status_v1,residual_persistence_v1,cost_dominance_v1
qwake_fp_baseline_registry=B0,B1,B2,B3,B4,B5,B6,B7
qwake_fp_paired_validation=P0,P1,P2
qwake_fp_cost_time_categories_exclusive=true
qwake_fp_role_matrix_inherited_from_qw1=true
qwake_fp_scientific_execution_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
qwake_next_stage=QW-3
```

## Consequences

- QW-3 may implement only the frozen registries and mappings;
- changing any field requires a new `contract_id`, digest, and separate decision
  before the scientific image freeze;
- negative opportunity, recognizability, safety, or net-cost findings remain
  admissible;
- the specification makes no transfer claim beyond this FixedPred special case.

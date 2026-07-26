# ADR-055: transition to `QW-LC2`

[Russian version](ADR-055-stage3b-qwake-lc2-transition.md)

- Status: accepted
- Date: 26 July 2026

## Context

The `QW-LC1` repository freeze was merged into `main` by commit
`9d073bc3c90eeda53ca03d0f7762b65da8749269` and independently verified. This completes `QW-LC1` and
permits only a separate transition to `QW-LC2` resource-model design.

`QW-LC2` must connect the [resource trajectory](../glossary_EN.md#term-resource-trajectory)
`Γ(a,s)` to the [cost vector](../glossary_EN.md#term-cost-vector) `C(a,s)` via
`Φ`, then define the separate [cost-equivalence](../glossary_EN.md#term-cost-equivalence)
operator `~C`.

## Decision

1. Materialize the two-file transition receipt
   `stage3b-qwake-lc2-transition-v1`.
2. Bind it to the `main` merge commit, the `QW-LC1` repository freeze, the
   `R(a,s)` schema, and their exact checksums.
3. Bound the future `QW-LC2` contract to three connected parts:
   - the `Γ(a,s)` measurement schema;
   - the `Φ: Γ -> C` mapping with no double counting;
   - `~C`, [Pareto admissibility](../glossary_EN.md#term-pareto-admissibility), and registered ambiguity resolution.
4. Define no fields, units, windows, thresholds, aggregation, scalarization,
   or empirical cost values in the transition.
5. Defer matched shadow validation, state identity, RNG,
   [fallback](../glossary_EN.md#term-fallback), implementation, and
   [execution](../glossary_EN.md#term-execution) to later slices.
6. Keep `QW-LC2` and all three definitions closed until this transition is
   merged.

## Verifiable boundary

```text
qwake_qw_lc1_complete=true
qwake_qw_lc2_transition_permitted=true
qwake_qw_lc2_transition_materialized=true
qwake_qw_lc2_transition_complete=false
qwake_qw_lc2_open=false
resource_trajectory_schema_open=false
measurement_to_cost_mapping_open=false
cost_equivalence_operator_definition_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC2-transition-merge
qwake_post_merge_next_slice=QW-LC2-resource-cost-contract
```

## Consequences

After merge and separate post-merge verification, the resource-and-cost
contract branch may be opened. This ADR is not a measurement model, makes no
mechanism-superiority claim, and permits no computational action.

# ADR-052: transition to `QW-LC1`

[Russian version](ADR-052-stage3b-qwake-lc1-transition.md)

- Status: accepted
- Date: 26 July 2026

## Context

The `QW-LC0` repository freeze was merged into `main` by commit
`0fbd54be337665e06ad63b6d9c7f8ca978ab75ee` and independently reverified. This completes
the preceding gate and permits a separate transition to `QW-LC1` design, but
it does not open `QW-LC1` content before this transition receipt is merged.

`QW-LC1` is limited to freezing the canonical
[required result](../glossary_EN.md#term-required-result) schema `R(a,s)`,
mandatory observables, and the
[response-equivalence](../glossary_EN.md#term-response-equivalence) operator
`~R`.

## Decision

1. Materialize the two-file transition receipt
   `stage3b-qwake-lc1-transition-v1`.
2. Bind it to the `main` merge commit, the `QW-LC0` repository freeze, the
   semantics contract, and their exact checksums.
3. Freeze the finite scope of the future `QW-LC1` slice:
   - canonical `R(a,s)` schema;
   - mandatory observables;
   - `~R` operator.
4. Defer the `Γ` trajectory schema, `Φ` mapping, [cost vector](../glossary_EN.md#term-cost-vector) `C`,
   implementation, bounded analytic-case validation, and
   [execution](../glossary_EN.md#term-execution) to later slices.
5. Keep `QW-LC1` and its required-response schema closed until the transition
   is merged.

## Verifiable boundary

```text
qwake_qw_lc0_repository_freeze_complete=true
qwake_qw_lc1_transition_permitted=true
qwake_qw_lc1_transition_materialized=true
qwake_qw_lc1_transition_complete=false
qwake_qw_lc1_open=false
qwake_qw_lc1_required_response_schema_open=false
mandatory_observables_definition_open=false
response_equivalence_operator_definition_open=false
resource_trajectory_schema_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC1-transition-merge
qwake_post_merge_next_slice=QW-LC1-required-response-schema
```

## Consequences

After merge and separate post-merge verification, the `QW-LC1` design branch
may be opened. This ADR defines neither schema fields nor `~R` tolerances,
`Γ` measurements, cost, code, or a computational campaign.

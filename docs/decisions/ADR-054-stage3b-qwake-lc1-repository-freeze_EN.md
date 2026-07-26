# ADR-054: `QW-LC1` repository freeze

[Русская версия](ADR-054-stage3b-qwake-lc1-repository-freeze.md)

- Status: accepted
- Date: 26 July 2026

## Context

Contract `stage3b-qwake-lc1-required-response-schema-v1` was recorded by commit
`de2b5a37583b22946073390caa244bee35dd793b` and merged into `main` by merge commit
`59e3143ba105a5b298e2cd551b221b8f6dae96f7`. Post-merge verification confirmed the first and second
parents, the exact 22-file scope, preservation of the schema tree, and the
contract and registry checksums.

Before `QW-LC1` can be completed, a separate
[integrity sealing](../glossary_EN.md#term-integrity-sealing) receipt must bind
the verified schema to a concrete `main` state. This freeze defines neither
`Γ`, `Φ`, cost, nor `~C`, and it does not permit the next slice before its own
merge and revalidation.

## Decision

1. Materialize a two-file `QW-LC1` repository-state receipt.
2. Bind it to the exact `main`, schema, and predecessor-transition commits.
3. Record the exact contract and registry checksums.
4. Preserve the schema and all predecessor
   [evidence](../glossary_EN.md#term-evidence) unchanged.
5. Keep `QW-LC1` incomplete and transition to `QW-LC2` prohibited until the
   receipt is merged.
6. Open neither [resource trajectory](../glossary_EN.md#term-resource-trajectory), cost mapping, implementation,
   [execution](../glossary_EN.md#term-execution), feature collection,
   oracle-label generation, the scientific image, test split, nor publication.

## Verifiable boundary

```text
qwake_qw_lc1_required_response_schema_merged=true
qwake_qw_lc1_schema_main_commit=59e3143ba105a5b298e2cd551b221b8f6dae96f7
qwake_qw_lc1_schema_commit=de2b5a37583b22946073390caa244bee35dd793b
qwake_qw_lc1_repository_freeze_materialized=true
qwake_qw_lc1_repository_freeze_complete=false
qwake_qw_lc1_complete=false
qwake_qw_lc2_transition_permitted=false
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
qwake_next_slice=QW-LC1-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC2-transition
```

## Consequences

A separate verification of the receipt on `main` is required after merge. Only
that verification may complete `QW-LC1` and permit an independent transition
to `QW-LC2`; this decision opens no resource schema, cost semantics, code, or
execution.

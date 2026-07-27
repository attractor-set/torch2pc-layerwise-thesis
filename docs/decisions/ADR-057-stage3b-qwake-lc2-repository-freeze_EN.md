# ADR-057: `QW-LC2` repository freeze

[Русская версия](ADR-057-stage3b-qwake-lc2-repository-freeze.md)

- Status: accepted
- Date: 26 July 2026

## Context

Contract `stage3b-qwake-lc2-resource-cost-contract-v1` was recorded by commit `3f1682765089b0819dcaaf9bb449c4c1bd155142` and
merged into `main` by merge commit `8f24229bcf19736086fe6f0340bda26dd533936a`. Post-merge verification confirmed
the exact parents, 20-file scope, tree preservation, and checksums.

Before `QW-LC2` can be completed, a separate
[integrity sealing](../glossary_EN.md#term-integrity-sealing) receipt must bind
the verified contract to a concrete `main` state.

## Decision

1. Materialize a two-file `QW-LC2` repository-state receipt.
2. Bind it to the exact `main`, contract, and `QW-LC2` transition commits.
3. Record the contract, registry, and transition-receipt checksums.
4. Preserve predecessor [evidence](../glossary_EN.md#term-evidence).
5. Keep `QW-LC2` incomplete and transition to `QW-LC3` prohibited until the
   receipt is merged and reverified.
6. Open neither implementation, [execution](../glossary_EN.md#term-execution),
   feature collection, oracle labels, the test split, nor publication.

## Verifiable boundary

```text
qwake_qw_lc2_resource_cost_contract_merged=true
qwake_qw_lc2_resource_cost_contract_complete=true
qwake_qw_lc2_contract_id=stage3b-qwake-lc2-resource-cost-contract-v1
qwake_qw_lc2_contract_sha256=sha256:313dc969ab59db20ee27976d3158fca23ce511801e0dc7700dde0d2d002ab69d
qwake_qw_lc2_repository_main_commit=8f24229bcf19736086fe6f0340bda26dd533936a
qwake_qw_lc2_resource_cost_commit=3f1682765089b0819dcaaf9bb449c4c1bd155142
qwake_qw_lc2_repository_freeze_materialized=true
qwake_qw_lc2_repository_freeze_complete=false
qwake_qw_lc2_complete=false
qwake_qw_lc3_transition_permitted=false
resource_trajectory_schema_frozen=true
measurement_to_cost_mapping_frozen=true
cost_equivalence_operator_definition_frozen=true
pareto_and_tie_break_rule_frozen=true
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
qwake_next_slice=QW-LC2-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC3-transition
```

## Consequences

Only post-merge receipt verification may complete `QW-LC2` and permit a
separate transition to `QW-LC3`. Implementation and execution remain closed.

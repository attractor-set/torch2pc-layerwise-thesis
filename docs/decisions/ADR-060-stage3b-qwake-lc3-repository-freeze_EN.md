# ADR-060: `QW-LC3` repository freeze

[Русская версия](ADR-060-stage3b-qwake-lc3-repository-freeze.md)

- Status: accepted
- Date: 27 July 2026

## Context

Contract `stage3b-qwake-lc3-matched-shadow-validation-contract-v1` was recorded
by commit `fb3f1cd4a4d3b4261db1179badcc1ccacddfe936` and merged through PR #121 into `main`
`71e73f56408c720334b8fa03e7133762c8bbcc43`. Post-merge verification confirmed the exact
parents, 14-file scope, tree preservation, and checksums.

Before `QW-LC3` can be completed, a separate
[integrity sealing](../glossary_EN.md#term-integrity-sealing) receipt must bind
the verified contract to a concrete `main` state.

## Decision

1. Materialize a two-file `QW-LC3` repository-state receipt.
2. Bind it to the exact `main`, contract, and `QW-LC3` transition commits.
3. Record the contract, registry, and transition-receipt checksums.
4. Preserve predecessor [evidence](../glossary_EN.md#term-evidence) unchanged.
5. Keep `QW-LC3` incomplete and `QW-LC4-I` implementation prohibited until
   the receipt is merged and reverified.
6. Open neither implementation, [execution](../glossary_EN.md#term-execution),
   feature collection, oracle labels, the test split, nor publication.

## Verifiable boundary

```text
qwake_qw_lc3_matched_shadow_validation_contract_merged=true
qwake_qw_lc3_matched_shadow_validation_contract_complete=true
qwake_qw_lc3_contract_id=stage3b-qwake-lc3-matched-shadow-validation-contract-v1
qwake_qw_lc3_contract_sha256=sha256:e1512f29b3e3e3882001172df360e895e6e628b8ea8e4103b9574990775dd5d8
qwake_qw_lc3_repository_main_commit=71e73f56408c720334b8fa03e7133762c8bbcc43
qwake_qw_lc3_contract_commit=fb3f1cd4a4d3b4261db1179badcc1ccacddfe936
qwake_qw_lc3_repository_freeze_materialized=true
qwake_qw_lc3_repository_freeze_complete=false
qwake_qw_lc3_complete=false
qwake_qw_lc4_implementation_permitted=false
matched_shadow_validation_protocol_frozen=true
opaque_state_ref_definition_frozen=true
rng_restoration_protocol_frozen=true
exact_reserve_suffix_validation_frozen=true
repeat_aggregation_protocol_frozen=true
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
qwake_next_slice=QW-LC3-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC4-I
```

## Consequences

Only post-merge receipt verification may complete `QW-LC3` and permit the
separate `QW-LC4-I` implementation slice. Execution and the scientific campaign
remain closed behind their own later boundaries.

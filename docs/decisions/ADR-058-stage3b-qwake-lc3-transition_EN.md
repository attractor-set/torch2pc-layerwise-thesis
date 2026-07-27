# ADR-058: transition to `QW-LC3`

[Russian version](ADR-058-stage3b-qwake-lc3-transition.md)

- Status: accepted
- Date: 26 July 2026

## Context

The `QW-LC2` repository freeze was merged into `main` as
`4f7c533047214398e7ec4dde9d58b5fc06964b90` and independently verified. Freeze
commit `3f4310a05de5b7cd3db0cdb5c8f7cf4bbcb09150` remains in the merge graph, the
tree is preserved, and the repository receipt and resource contract have their
expected checksums. This completes `QW-LC2` and permits only a separate
transition into `QW-LC3` validation design.

`QW-LC3` must connect the already frozen [required
result](../glossary_EN.md#term-required-result) `R(a,s)` and [cost
vector](../glossary_EN.md#term-cost-vector) `C(a,s;r,p)` to a protocol that
compares `LOCAL_SWEEP` and `ANALYTIC_COMPLETION` from one state, restores random
number generators, and retains a complete exact-reserve suffix.

## Decision

1. Materialize the two-file transition receipt
   `stage3b-qwake-lc3-transition-v1`.
2. Bind it to the `main` merge commit, the `QW-LC2` repository freeze, the
   resource-cost contract, the required-response schema, and their exact
   checksums.
3. Limit the future `QW-LC3` contract to:
   - a matched shadow-validation protocol;
   - construction and validation of the shared opaque state reference;
   - RNG snapshot, restoration, and post-state checks;
   - complete exact-reserve suffix validation;
   - repeat order and matched aggregation.
4. Do not define snapshot serialization, the RNG inventory, arm order, repeat
   count, tolerances, aggregators, measurement windows, or pass criteria in the
   transition.
5. Do not open [candidate](../glossary_EN.md#term-candidate) implementation,
   [runtime](../glossary_EN.md#term-runtime) authorization, engineering
   [execution](../glossary_EN.md#term-execution), feature collection,
   oracle-label generation, policy activation,
   scientific execution, the test split, or publication.
6. Keep `QW-LC3` and all of its definitions closed until transition merge.

## Verifiable boundary

```text
qwake_qw_lc2_repository_freeze_complete=true
qwake_qw_lc2_complete=true
qwake_qw_lc3_transition_permitted=true
qwake_qw_lc3_transition_materialized=true
qwake_qw_lc3_transition_complete=false
qwake_qw_lc3_open=false
matched_shadow_validation_protocol_open=false
opaque_state_ref_definition_open=false
rng_restoration_protocol_open=false
exact_reserve_suffix_validation_open=false
repeat_aggregation_protocol_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
qwake_next_slice=QW-LC3-transition-merge
qwake_post_merge_next_slice=QW-LC3-matched-shadow-validation-contract
```

## Consequences

After merge and separate post-merge verification, a matched shadow-validation
contract branch may be opened. This ADR does not establish mechanism
equivalence, activate the `end_to_end_v1` profile, or authorize computation.

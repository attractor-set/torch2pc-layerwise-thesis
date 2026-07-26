# ADR-053: `QW-LC1` required-response schema

[Russian version](ADR-053-stage3b-qwake-lc1-required-response-schema.md)

- Status: accepted
- Date: 26 July 2026

## Context

The `QW-LC1` transition was merged into `main` by commit `c3533fcb63ffc869faddbaa99645c9099d16d1cc` and
independently reverified. Only the slice that freezes the canonical
[required result](../glossary_EN.md#term-required-result) schema `R(a,s)`,
mandatory observables, and the operational
[response-equivalence](../glossary_EN.md#term-response-equivalence) predicate
`~R` is permitted.

The schema must compare `LOCAL_SWEEP` and `ANALYTIC_COMPLETION` without
identifying the response with the
[computational mechanism](../glossary_EN.md#term-computational-mechanism),
[resource trajectory](../glossary_EN.md#term-resource-trajectory), or
[cost vector](../glossary_EN.md#term-cost-vector).

## Decision

1. Freeze contract `stage3b-qwake-lc1-required-response-schema-v1`.
2. Define `R(a,s)` as the ordered triple:
   - named parameter gradients;
   - [endpoint](../glossary_EN.md#term-endpoint) beliefs in registered layer order;
   - scalar endpoint loss.
3. Define canonical serialization as a JSON manifest plus separate
   little-endian C-contiguous payload files without numerical casting.
4. Require structural fields, manifests, finiteness flags, and SHA-256 for each
   payload and the complete response.
5. Apply exact structural gates before numerical comparison. Compare each
   registered entry independently after conversion to `float64`.
6. Freeze a zero-safe rule:
   - two inactive entries pass the cosine gate but must pass `relative_l2` and
     `max_abs`;
   - one active and one inactive entry always fail;
   - two active entries must additionally pass `min_cosine`.
7. Freeze `cpu_float64_engineering` and `rocm_float32_canonical` profiles;
   ROCm/float32 remains decision-facing.
8. Do not assume `~R` is transitive and do not construct equivalence classes
   without a separately frozen closure.
9. Defer state/RNG/[fallback](../glossary_EN.md#term-fallback) matching to `QW-LC3`, and `Γ`, `Φ`, `C`, and `~C`
   to `QW-LC2`.
10. Keep implementation and [execution](../glossary_EN.md#term-execution)
    closed.

## The `~R` operator

After the exact structural gate, compute for every entry:

```text
difference_l2 = ||candidate - reference||_2
max_abs       = ||candidate - reference||_∞
scale         = max(||reference||_2, ||candidate||_2, zero_atol)
relative_l2   = difference_l2 / scale
```

For two active entries, also compute cosine. The normalized response defect is
the maximum defect over all entries; accept only when `d_R <= 1`. Exact SHA-256
equality is sufficient but not required for `~R`.

## Verifiable boundary

```text
qwake_qw_lc1_transition_complete=true
qwake_qw_lc1_open=true
qwake_qw_lc1_required_response_schema_frozen=true
qwake_qw_lc1_contract_id=stage3b-qwake-lc1-required-response-schema-v1
qwake_qw_lc1_contract_sha256=sha256:c7923249c538b29a34f8ffcfcac987b9925a911eb107a085a166ab1d7ca22992
mandatory_observables_definition_frozen=true
response_equivalence_operator_definition_frozen=true
qwake_qw_lc1_complete=false
qwake_qw_lc2_transition_permitted=false
resource_trajectory_schema_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC1-repository-freeze
```

## Consequences

The contract freezes only the response form and comparison rule. It establishes
neither analytic-[candidate](../glossary_EN.md#term-candidate) equivalence, implementation correctness, safety,
coverage, cost saving, nor transfer beyond the registered case. The next
permitted slice is a separate `QW-LC1` repository-state freeze.

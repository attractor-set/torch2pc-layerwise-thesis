# ADR-059: `QW-LC3` matched shadow-validation contract

[Russian version](ADR-059-stage3b-qwake-lc3-matched-shadow-validation-contract.md)

- Status: accepted
- Date: July 27, 2026

## Context

The `QW-LC3` transition was merged through PR #120 into `main`
`a7e0c4ec1978042d68abc7437e3005e4295e75ff` and independently verified. The
transition commit `a8993e3a996317eeb44270ee37e0e879537d5d65` remains the second
parent, the tree is preserved, and the transition receipt has the expected
checksums. Only a contract that connects the already frozen
[required result](../glossary_EN.md#term-required-result) `R`,
[resource trajectory](../glossary_EN.md#term-resource-trajectory) `Γ`, and
[cost vector](../glossary_EN.md#term-cost-vector) `C` to a matched validation
protocol for the two `LOCAL_COMPUTE` mechanisms is permitted.

The contract contains no `ANALYTIC_COMPLETION` implementation, invokes no
model, and creates no engineering or scientific
[evidence](../glossary_EN.md#term-evidence).

## Decision

1. Freeze contract
   `stage3b-qwake-lc3-matched-shadow-validation-contract-v1`.
2. Define `opaque_state_ref` as the `SHA-256` of a canonical shared-state
   manifest with ordered digests for inputs, targets, parameters, buffers,
   decision-epoch beliefs, optional update state, and deterministic [runtime](../glossary_EN.md#term-runtime)
   controls.
3. Create every arm and reserve probe from a fresh disposable fork of the
   immutable snapshot. Any source mutation, missing payload, or state-reference
   mismatch fails closed.
4. Freeze a complete RNG inventory for CPU and ROCm. Restore the same snapshot
   before every arm and reserve probe. Every additional generator must be
   registered. The two arms' post-RNG states must match exactly within every
   pair, and the process pre-cell state is restored after the cell.
5. Use twelve matched repeats. Arm order alternates exactly: six repeats begin
   with `LOCAL_SWEEP`, and six begin with `ANALYTIC_COMPLETION`.
6. Require `~R` to pass for every pair; majority voting and repeat exclusion are
   forbidden. Exact response-digest equality is sufficient but not required for
   `~R`.
7. Require complete `Γ` and `C` for every normal arm. Reserve-probe cost remains
   separate and is excluded from normal [candidate](../glossary_EN.md#term-candidate) aggregation.
8. Validate the reserve path with two forced probes, before the first and after
   the final repeat. Candidate failure is injected before its disposable state
   is mutated. The reserve path must execute the complete ordered
   `LOCAL_SWEEP` suffix without skips, duplicates, or candidate intermediate
   state; its canonical response must exactly match the direct exact reference.
9. Aggregate cost only componentwise over paired differences
   `ANALYTIC_COMPLETION - LOCAL_SWEEP`: median, lower and upper hinges, minimum,
   and maximum. Scalarization, outlier removal, missing-value imputation, and
   statistical-significance claims are forbidden.
10. Test residual order effect separately for each action by comparing
    componentwise medians in first and second positions with the registered
    `QW-LC2` tolerances.
11. Do not require cost superiority for contract pass and do not permit policy
    activation. Future `end_to_end_v1` measurement is eligible only after all
    control gates in this contract pass.
12. Keep implementation, [execution](../glossary_EN.md#term-execution), feature
    collection, oracle-label generation, scientific campaign, test data, and
    publication closed.

## Verifiable boundary

```text
qwake_qw_lc3_transition_complete=true
qwake_qw_lc3_open=true
qwake_qw_lc3_matched_shadow_validation_contract_frozen=true
qwake_qw_lc3_contract_id=stage3b-qwake-lc3-matched-shadow-validation-contract-v1
qwake_qw_lc3_contract_sha256=sha256:e1512f29b3e3e3882001172df360e895e6e628b8ea8e4103b9574990775dd5d8
matched_shadow_validation_protocol_frozen=true
opaque_state_ref_definition_frozen=true
rng_restoration_protocol_frozen=true
exact_reserve_suffix_validation_frozen=true
repeat_aggregation_protocol_frozen=true
qwake_qw_lc3_complete=false
qwake_qw_lc4_implementation_permitted=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
qwake_next_slice=QW-LC3-repository-freeze
```

## Consequences

The contract defines a future validation but reports no validation result. It
does not establish analytic-candidate [response equivalence](../glossary_EN.md#term-response-equivalence), savings,
implementation correctness, or policy safety. The next permitted slice is a
separate `QW-LC3` repository freeze.

# ADR-056: `QW-LC2` resource and cost contract

[Russian version](ADR-056-stage3b-qwake-lc2-resource-cost-contract.md)

- Status: accepted
- Date: 26 July 2026

## Context

The `QW-LC2` transition was merged into `main` by commit `858403cbb2423ad3427ab7a042266880ca34c0b7`
and independently verified. Only a separate contract defining the
[resource trajectory](../glossary_EN.md#term-resource-trajectory)
`Γ(a,s;r,p)`, `Φ: Γ -> C`, the [cost vector](../glossary_EN.md#term-cost-vector)
`C(a,s;r,p)`, and the separate
[cost-equivalence](../glossary_EN.md#term-cost-equivalence) operator `~C` is
permitted.

The contract preserves the distinction between response `R`, mechanism `M`,
raw measurements `Γ`, and decision vector `C`, prohibits hidden scalarization
and double counting, and prevents the engineering shadow profile from being
reported as an end-to-end estimate.

## Decision

1. Freeze contract `stage3b-qwake-lc2-resource-cost-contract-v1`.
2. Define `Γ(a,s;r,p)` as canonical `JSON` containing identity, one root
   monotonic interval, ordered intervals for five owners, memory peaks,
   artifact records, observer calibration, and a
   [fallback](../glossary_EN.md#term-fallback) record.
3. Use owners `core_compute`, `diagnostic_mechanism`, `observer`,
   `control_plane`, and `fallback`; every interval has exactly one owner.
4. Define `Φ` as a fieldwise mapping into an ordered 11-field `C`: primary
   compute time, end-to-end latency, two memory peaks, diagnostic time and
   bytes, observer overhead and [evidence](../glossary_EN.md#term-evidence)
   bytes, control time, fallback time, and an exact fallback flag.
5. Prevent double counting: use interval unions, keep latency as an independent
   inclusive component, use maxima for memory, count artifact bytes once by
   `SHA-256`, and never subtract observer overhead from latency or compute.
6. Map [observer cost](../glossary_EN.md#term-observer-cost) as
   `max(0, instrumented-control)`; preserve a negative raw residual as
   over-closure and never call it negative physical cost.
7. Freeze two cost profiles:
   - `shadow_mechanism_v1`, engineering and non-decision-facing;
   - `end_to_end_v1`, a future decision-facing profile requiring `QW-LC3`.
8. Permit comparison only within one state binding, lane profile, and cost
   profile. CPU/ROCm cross-lane comparison is forbidden.
9. Define `~C` fieldwise by
   `|x-y| <= atol + rtol*max(|x|,|y|)` with registered time, peak, artifact,
   and Boolean tolerance classes. Transitivity of `~C` is not assumed.
10. Apply cost only after `~R` admission. Use
    [Pareto admissibility](../glossary_EN.md#term-pareto-admissibility) without
    scalarization and deterministic ambiguity resolution: no fallback,
    latency, compute, peak allocated, then lexical action ID.
11. Use the fail-closed exact reserve path `LOCAL_SWEEP` for a missing or
    incomplete vector.
12. Defer state identity, RNG restoration, matched shadow validation, fallback
    suffix validation, and repeat aggregation to `QW-LC3`.
13. Keep implementation, [execution](../glossary_EN.md#term-execution), feature
    collection, oracle labels, policy activation, the test split, and
    publication closed.

## Tolerance profiles

```text
cpu_float64_engineering:
  time_ns:     atol=50000, rtol=0.10
  peak_bytes:  atol=4096,  rtol=0.02
  artifact_bytes: exact

rocm_float32_canonical:
  time_ns:     atol=10000, rtol=0.05
  peak_bytes:  atol=4096,  rtol=0.01
  artifact_bytes: exact
```

These tolerances define operational cost proximity within one registered lane
and profile. They are not statistical confidence intervals and permit no
cross-device transfer.

## Verifiable boundary

```text
qwake_qw_lc2_transition_complete=true
qwake_qw_lc2_open=true
qwake_qw_lc2_resource_cost_contract_frozen=true
qwake_qw_lc2_contract_id=stage3b-qwake-lc2-resource-cost-contract-v1
qwake_qw_lc2_contract_sha256=sha256:313dc969ab59db20ee27976d3158fca23ce511801e0dc7700dde0d2d002ab69d
resource_trajectory_schema_frozen=true
measurement_to_cost_mapping_frozen=true
cost_equivalence_operator_definition_frozen=true
pareto_and_tie_break_rule_frozen=true
qwake_qw_lc2_complete=false
qwake_qw_lc3_transition_permitted=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC2-repository-freeze
```

## Consequences

The contract defines the measurement and comparison form but does not establish
[candidate](../glossary_EN.md#term-candidate) equivalence, savings,
instrumentation correctness, or fallback sufficiency. The next permitted slice
is a separate `QW-LC2` repository-state freeze.

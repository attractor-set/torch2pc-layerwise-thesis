# `QWake-FP` extension for local-compute mechanism selection

[Русская версия](qwake-local-compute-extension.md)

**Status:** `QW-4B-DOC-R1` design freeze; implementation and
[execution](glossary_EN.md#term-execution) are closed.

## 1. Reason for revision

The previous active roadmap did not separate the computational result, the way
that result was obtained, and the resources actually used. That conflation
cannot rigorously compare two methods that return the same answer through
different computational paths and at different cost.

The new model is introduced before a new container image and before
re-authorization. The old preflight and authorization are retained only as an
audit record and cannot be reused.

## 2. Four independent objects

For each state `s` and action `a`, distinguish:

1. the [required result](glossary_EN.md#term-required-result) `R(a,s)`;
2. the [computational mechanism](glossary_EN.md#term-computational-mechanism) `M(a)`;
3. the [resource trajectory](glossary_EN.md#term-resource-trajectory) `Γ(a,s)`;
4. the [cost vector](glossary_EN.md#term-cost-vector) `C(a,s)=Φ(Γ(a,s))`.

The required result determines neither a unique mechanism nor a unique resource
trajectory. Response equality is therefore not [evidence](glossary_EN.md#term-evidence) of equal computational
cost.

## 3. Two equivalence relations

[Response equivalence](glossary_EN.md#term-response-equivalence) is defined
relative to the registered response:

```math
a_i \sim_R a_j
\iff
R(a_i,s) \approx_R R(a_j,s)
```

[Cost equivalence](glossary_EN.md#term-cost-equivalence) is defined separately:

```math
a_i \sim_C a_j
\iff
C(a_i,s) \approx_C C(a_j,s)
```

The following case is admissible:

```math
a_{explicit} \sim_R a_{analytic}
a_{explicit} \not\sim_C a_{analytic}
```

It denotes the same required response with distinguishable computational
structure and cost. It does not claim that the result is independent of
computational resources.

## 4. The `LOCAL_COMPUTE` family

[Local compute](glossary_EN.md#term-local-compute) is an action family rather
than one algorithm:

```text
LOCAL_COMPUTE
├── LOCAL_SWEEP
└── ANALYTIC_COMPLETION
```

An explicit local sweep performs an explicit registered
update over a bounded aggregate. [Analytic completion](glossary_EN.md#term-analytic-completion)
obtains the same registered response without explicitly replaying the full
computational sequence when that property is demonstrated for a bounded case.

Both mechanisms must preserve the same response boundary, [artifact provenance](glossary_EN.md#term-provenance),
cost rules, and exact-reserve-path availability.

## 5. Action admission

The admissible action set is defined by a bound on
[decision regret](glossary_EN.md#term-decision-regret):

```math
\mathcal A_{adm}(s)=\{a:\operatorname{Regret}_R(a,s)\le\varepsilon\}
```

Selection occurs only within this set:

```math
a^*(s)=\arg\min_{a\in\mathcal A_{adm}(s)} C(a,s)
```

If registered cost components do not permit scalar comparison, use
[Pareto admissibility](glossary_EN.md#term-pareto-admissibility) and a
preregistered ambiguity-resolution rule.

## 6. Bounded analytic candidate

The first [candidate](glossary_EN.md#term-candidate) identifier is:

```text
fixedpred_eta1_wavefront_completion_v1
```

Its scope is simultaneously restricted to:

```text
algorithm=FixedPred
eta=1
architecture=lenet_classic
executor=stage2_baseline
mode=shadow_post_action_validation
```

It may emit only final gradients and preregistered observables. `Strict`,
arbitrary `eta`, arbitrary graphs, skip connections, a universal symbolic
solver, and full-trajectory reconstruction remain outside scope.

## 7. Stage sequence

```text
QW-4B-DOC-R1
→ new immutable baseline image
→ QW-4B-F-v2
→ QW-4B-E-v2
→ sealed baseline report
→ QW-LC0
→ QW-LC1
→ QW-LC2
→ QW-LC3
→ QW-LC4-I
→ QW-LC4-F
→ QW-LC4-E
→ QW-5
→ C1
→ C2
→ C3
→ R
```

`QW-LC0` freezes semantics and scope. `QW-LC1` freezes observable responses.
`QW-LC2` freezes the resource model. `QW-LC3` defines matched validation.
`QW-LC4-I`, `QW-LC4-F`, and `QW-LC4-E` separate implementation,
authorization, and engineering execution. Only a successful extension report
permits `QW-5`, the single scientific-image freeze.

## 8. Current boundary

```text
qwake_documentation_refactor_complete=true
qwake_old_runtime_authorization_retired=true
qwake_new_image_required=true
qwake_new_runtime_preflight_captured=false
qwake_new_runtime_authorization_issued=false
qwake_runtime_validation_performed=false
qwake_engineering_evidence_present=false
qwake_local_compute_contract_frozen=true
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
qwake_scientific_image_freeze_permitted=false
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
test_dataset_access=false
publication_permitted=false
```


## 9. Post-merge opening of `QW-LC0`

The [baseline](glossary_EN.md#term-baseline) report repository evidence is sealed on `main`
`4f23b752a40ae05de9fc7ee49c9962c44083b71d`. Therefore only the next documentation operation is
permitted: the final freeze of `R/M/Γ/C` semantics, the `LOCAL_COMPUTE` scope,
the first analytic candidate, and the non-generalization boundaries.

```text
qwake_qw4b_e_v2_repository_evidence_sealed=true
qwake_qw_lc0_open=true
qwake_qw_lc0_semantics_scope_frozen=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
qwake_next_slice=QW-LC0
qwake_post_lc0_next_slice=QW-LC1
```

Opening `QW-LC0` does not authorize model invocation, feature collection,
post-action oracle generation, local-sweep execution, or analytic completion.


## 10. Normative `QW-LC0` freeze

Contract `stage3b-qwake-lc0-semantics-scope-v1` makes the `R/M/Γ/C` separation normative for
`LOCAL_COMPUTE`. `LOCAL_SWEEP` and `ANALYTIC_COMPLETION` are distinct
mechanisms; equality of their required result does not imply equality of their
resource trajectory or cost.

This slice does not define the final response serialization, resource
measurement schema, or cost map. Those fields belong to `QW-LC1` and `QW-LC2`.
The first candidate remains an unvalidated hypothesis within a strictly bounded
scope.

```text
qwake_qw_lc0_semantics_scope_frozen=true
qwake_qw_lc1_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
qwake_next_slice=QW-LC0-repository-freeze
qwake_post_merge_next_slice=QW-LC1
```

## 11. `QW-LC0` repository freeze

After the contract merge into `main` `8429f54257685a879b0a44499d5fa81eab7310ea`, a separate
receipt records the exact commits and checksums. Materializing it does not
permit transition to `QW-LC1` before its own merge and revalidation.

```text
repository_freeze_materialized=true
repository_freeze_complete=false
qw_lc1_transition_permitted=false
qw_lc1_open=false
local_compute_implementation_open=false
local_compute_execution_open=false
```

## 12. Transition to `QW-LC1`

The transition fixes only the scope of the next definition: the canonical
`R(a,s)` schema, mandatory observables, and `~R`. It defines no fields,
tolerances, or comparison algorithm and opens neither `Γ`, `Φ`, cost, code,
nor execution.

```text
lc1_transition_materialized=true
lc1_transition_complete=false
lc1_open=false
required_response_schema_open=false
resource_trajectory_schema_open=false
local_compute_implementation_open=false
local_compute_execution_open=false
```
## 13. `QW-LC1` required-response schema

Contract `stage3b-qwake-lc1-required-response-schema-v1` freezes `R(a,s)` as the ordered collection of named
parameter gradients, [endpoint](glossary_EN.md#term-endpoint) beliefs, and scalar loss. The response is
serialized as a canonical JSON manifest plus separate little-endian
C-contiguous payload files that preserve the source dtype.

Before numerical comparison, schema/state/profile, component order, keys,
positions, shapes, dtypes, and `numel` must match exactly. Each entry is then
compared in `float64` by `relative_l2`, `max_abs`, and cosine only when both
entries are active. Two inactive entries pass the cosine gate; one active and
one inactive entry always fail.

```text
required_result_components=
  named_parameter_gradients,
  endpoint_beliefs,
  endpoint_loss
canonical_profile=rocm_float32_canonical
engineering_profile=cpu_float64_engineering
response_equivalence_transitivity_assumed=false
resource_trajectory_schema_open=false
local_compute_implementation_open=false
local_compute_execution_open=false
next_slice=QW-LC1-repository-freeze
```
## 14. `QW-LC1` repository freeze

After the schema merge into `main` `59e3143ba105a5b298e2cd551b221b8f6dae96f7`, a separate receipt records
the exact commits and contract checksums. Materializing the receipt neither
completes `QW-LC1` nor permits transition to `QW-LC2` before its own merge and
revalidation.

```text
repository_freeze_materialized=true
repository_freeze_complete=false
qw_lc1_complete=false
qw_lc2_transition_permitted=false
resource_trajectory_schema_open=false
measurement_to_cost_mapping_open=false
cost_equivalence_operator_definition_open=false
local_compute_implementation_open=false
local_compute_execution_open=false
```

## 15. Transition to `QW-LC2`

After `QW-LC1` completion, the transition bounds the next contract to three
parts: the `Γ(a,s)` measurement schema, `Φ: Γ -> C`, and `~C`. The transition
defines no measured fields, units, windows, aggregation, thresholds,
scalarization, or empirical values. Matched validation, state, RNG,
[fallback](glossary_EN.md#term-fallback), code, and execution remain later
slices.

```text
lc1_complete=true
lc2_transition_materialized=true
lc2_transition_complete=false
lc2_open=false
resource_trajectory_schema_open=false
measurement_to_cost_mapping_open=false
cost_equivalence_operator_definition_open=false
local_compute_implementation_open=false
local_compute_execution_open=false
```

## 16. `QW-LC2` resource and cost contract

Contract `stage3b-qwake-lc2-resource-cost-contract-v1` freezes resource trajectory `Γ(a,s;r,p)` as an
ordered record of identity, root interval, interval ownership, memory peaks,
unique artifact bytes, observer calibration, and fallback. `Φ` produces `C`
in this order:

```text
compute_primary_time_ns
latency_wall_time_ns
peak_allocated_bytes
peak_reserved_bytes
diagnostic_primary_time_ns
diagnostic_materialized_bytes
observer_overhead_time_ns
observer_evidence_bytes
control_wall_time_ns
fallback_wall_time_ns
fallback_invoked
```

Latency remains an independent inclusive component and is not added to
decomposed times. Intervals are unioned, memory uses maxima, artifact bytes are
counted once by owner and SHA-256, and observer overhead is not subtracted from
latency or compute.

`shadow_mechanism_v1` is not decision-facing. Future `end_to_end_v1` requires
completed `QW-LC3`. `~C` applies only within identical opaque state binding,
lane profile, and cost profile; transitivity is not assumed. After `~R`
admission, tolerance-aware Pareto and the registered tie-break apply. A missing
or incomplete cost vector selects `LOCAL_SWEEP`.

```text
resource_trajectory_schema_frozen=true
measurement_to_cost_mapping_frozen=true
cost_equivalence_operator_definition_frozen=true
pareto_and_tie_break_rule_frozen=true
qwake_qw_lc2_complete=false
qwake_qw_lc3_transition_permitted=false
local_compute_implementation_open=false
local_compute_execution_open=false
```

## 17. `QW-LC2` repository freeze

The receipt binds `stage3b-qwake-lc2-resource-cost-contract-v1` to merge commit `8f24229bcf19736086fe6f0340bda26dd533936a`, first parent
`858403cbb2423ad3427ab7a042266880ca34c0b7`, and contract commit `3f1682765089b0819dcaaf9bb449c4c1bd155142`. It confirms
preservation of `Γ`, `Φ`, `C`, `~C`, profiles, and rules, but contains no
implementation and permits no execution.

```text
qwake_qw_lc2_repository_freeze_materialized=true
qwake_qw_lc2_repository_freeze_complete=false
qwake_qw_lc3_transition_permitted=false
local_compute_implementation_open=false
local_compute_execution_open=false
```

## 18. Transition to `QW-LC3`

After the `QW-LC2` repository freeze was merged into `main`
`4f7c533047214398e7ec4dde9d58b5fc06964b90` and separately verified, `QW-LC2`
is complete. The transition receipt limits the next contract to matched shadow
validation, construction of an opaque shared-state reference, RNG restoration,
complete exact-reserve suffix validation, and matched repeat aggregation.

The transition does not define snapshot serialization, the RNG inventory, arm
order, repeat count, tolerances, or pass criteria. It does not open
implementation, authorization, or execution.

```text
qwake_qw_lc2_complete=true
qwake_qw_lc3_transition_materialized=true
qwake_qw_lc3_transition_complete=false
qwake_qw_lc3_open=false
matched_shadow_validation_protocol_open=false
opaque_state_ref_definition_open=false
rng_restoration_protocol_open=false
exact_reserve_suffix_validation_open=false
repeat_aggregation_protocol_open=false
local_compute_implementation_open=false
local_compute_execution_open=false
next_slice=QW-LC3-transition-merge
post_merge_next_slice=QW-LC3-matched-shadow-validation-contract
```

## 19. `QW-LC3` matched shadow-validation contract

Contract `stage3b-qwake-lc3-matched-shadow-validation-contract-v1` connects
`R`, `Γ`, and `C` in one execution-closed validation construction. The shared
snapshot receives a canonical `opaque_state_ref`; every arm and reserve probe
receives a fresh disposable fork. Every registered RNG is restored before each
arm, and the two arms' post-RNG states must match exactly within each pair.

Each validation cell has twelve pairs with alternating arm order. Every pair
must pass `~R`; a missing or excluded repeat fails the cell closed. Two forced
probes verify, before the first and after the final repeat, that the complete
reserve `LOCAL_SWEEP` executes the full suffix without skips, duplicates, or
candidate intermediate state.

Cost is aggregated separately for each field as the paired difference
`ANALYTIC_COMPLETION - LOCAL_SWEEP`; median, lower and upper hinges, minimum,
and maximum are retained. A scalar total and statistical-significance claim are
forbidden. The contract implements no mechanism and authorizes no execution.

```text
qwake_qw_lc3_matched_shadow_validation_contract_frozen=true
matched_shadow_validation_protocol_frozen=true
opaque_state_ref_definition_frozen=true
rng_restoration_protocol_frozen=true
exact_reserve_suffix_validation_frozen=true
repeat_aggregation_protocol_frozen=true
qwake_qw_lc3_complete=false
qwake_qw_lc4_implementation_permitted=false
local_compute_implementation_open=false
local_compute_execution_open=false
next_slice=QW-LC3-repository-freeze
```

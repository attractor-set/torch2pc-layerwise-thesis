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

## 20. `QW-LC3` repository freeze

After contract merge through PR #121 into `main` `71e73f56408c720334b8fa03e7133762c8bbcc43`, a separate
receipt binds the verified tree to contract commit `fb3f1cd4a4d3b4261db1179badcc1ccacddfe936`, the
`QW-LC3` transition, and their checksums. Receipt materialization does not
complete `QW-LC3` before its own merge and reverification.

```text
qwake_qw_lc3_repository_freeze_materialized=true
qwake_qw_lc3_repository_freeze_complete=false
qwake_qw_lc3_complete=false
qwake_qw_lc4_implementation_permitted=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
qwake_next_slice=QW-LC3-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC4-I
```

## 21. `QW-LC4-I` bounded implementation

After the `QW-LC3` repository freeze merged into `main`
`7c6cbb6ba4941cf78b2bfec3e6e8955c2830a58b`, the bounded implementation
materializes the first code for the registered `ANALYTIC_COMPLETION` candidate.
At candidate index `t`, the completed wavefront supplies the boundary residual;
only the unfinished lower VJP chain is propagated. The exact reference executes
all remaining FixedPred sweeps from another disposable fork.

The same module materializes `opaque_state_ref`, complete RNG restoration, the
`QW-LC1` response predicate, the `QW-LC2` non-scalar cost mapping, two forced
exact-reserve probes, the balanced twelve-repeat schedule, and componentwise
paired aggregation. A synthetic-only authorization is deliberately separate
from every future [runtime](glossary_EN.md#term-runtime) authorization.

```text
qw_lc3_complete=true
qw_lc4_i_implementation_materialized=true
synthetic_unit_test_only=true
local_compute_implementation_open=false
local_compute_execution_open=false
scientific_execution_open=false
next_slice=QW-LC4-I-merge
post_merge_next_slice=QW-LC4-F
```

## 22. `QW-LC4-F` runtime-freeze authoring

After `QW-LC4-I` merged through PR #123 into `main`
`c9f3dadcd5330887584b8bf71d906c667dacf076`, the runtime-freeze authoring layer
is materialized. It adds an adapter for already captured FixedPred state, a
deny-all preflight, an exact one-[attempt](glossary_EN.md#term-attempt) engineering authorization schema, and
a sealing procedure with no runtime executor.

The request freezes two lanes, seven candidate indices, twelve repeats per
combination, and two reserve probes. This yields 14 runtime cells, 168
matched-pair cells, and 28 reserve probes. No cell is executed in the authoring
slice.

The freeze is split into two phases because the image digest must belong to the
commit that contains the adapter and admission code. The authoring code is
first verified and committed; an immutable image is then built from that commit
and the actual preflight, authorization, and validation receipts are
materialized.

```text
qw_lc4_i_complete=true
qw_lc4_f_authoring_materialized=true
qw_lc4_f_request_frozen=true
qw_lc4_f_materialized=false
qw_lc4_e_branch_permitted=false
local_compute_execution_open=false
runtime_execution_performed=false
scientific_execution_open=false
next_slice=QW-LC4-F-authoring-commit
post_commit_next_slice=QW-LC4-F-runtime-materialization
```
## `QW-LC4-F`: authorization frozen without execution

[ADR-063](decisions/ADR-063-stage3b-qwake-lc4-f-runtime-freeze_EN.md) binds
the bounded implementation to the exact image, CPU/ROCm checks, static
receipt, and one-attempt authorization. The freeze covers 14 runtime cells,
168 matched cells, and 28 reserve probes.

`runtime_execution_permitted=true` inside authorization does not open
execution on the freeze branch. `QW-LC4-E` is permitted only after merge and
independent verification of `QW-LC4-F`.
## `QW-LC4-E`: separate admission before execution

[ADR-064](decisions/ADR-064-stage3b-qwake-lc4-e-execution-admission-authoring_EN.md)
separates frozen authorization, verified control-plane admission, and actual
execution start. This slice materializes only the schema and validator; no
execution lease or executor exists.
## `QW-LC4-E`: concrete admission freeze

[ADR-065](decisions/ADR-065-stage3b-qwake-lc4-e-execution-admission-freeze_EN.md)
freezes an admission record bound to `main` `bce821dff0729629db0ccb306d8f3fd1dd9a2e13`. Its one-attempt
permission does not open the branch-level execution gate. No lease, executor,
results, or evidence exists.
## `QW-LC4-E`: lease and wrapper contract authoring

[ADR-066](decisions/ADR-066-stage3b-qwake-lc4-e-execution-lease-wrapper-authoring_EN.md)
introduces a prospective one-attempt lease and wrapper effect contract. Both
objects exist only in memory; no lease file, executor, output root, or evidence
exists.

## `QW-LC4-E`: atomic lease/wrapper implementation

[ADR-067](decisions/ADR-067-stage3b-qwake-lc4-e-execution-lease-wrapper-implementation_EN.md)
adds effect mechanics in a separate module while preserving the frozen
authoring module. The lease name is claimed with a same-directory temporary
file, `fsync`, and a no-replace hard link. Output absence is checked again
after the claim, so a race consumes the lease and blocks backend invocation.

The backend is confined to a hidden staging tree. Symlinks, non-regular files,
empty output, and invalid receipts fail closed. A complete synchronized tree is
promoted with `renameat2(RENAME_NOREPLACE)`. Failure removes only staging while
the lease persists and retry remains prohibited.

The verifier exercises this path under `/tmp` only. Repository execution,
evidence, science, test-data access, and publication remain closed pending a
separate freeze of the exact implementation commit.
## `QW-LC4-E`: execution-freeze authoring

See [ADR-068](decisions/ADR-068-stage3b-qwake-lc4-e-execution-freeze-authoring_EN.md).

- PR #128 merged into `main` as `24966cd2a0380e46ab1924ff4ab8987f17e1fe9e`;
- the exact 16-file implementation tree, SHA-256 identities, and CI 2/2 passed;
- the deterministic request binds implementation, admission, lease/output
  paths, 168 cells, and 28 reserve probes;
- claim and execution must occur in one process without retry;
- the concrete backend and one-shot entrypoint remain absent;
- execution freeze, lease, execution, engineering evidence, and publication
  remain closed;
- the post-merge next slice is `QW-LC4-E-runtime-backend-implementation`.

## `QW-LC4-E`: bounded backend and negative-outcome preservation

See [ADR-069](decisions/ADR-069-stage3b-qwake-lc4-e-runtime-backend-implementation_EN.md).

The concrete backend binds the frozen matrix to `lenet_classic`, the synthetic
batch, the exact `LOCAL_SWEEP` suffix, and `ANALYTIC_COMPLETION`. Numerical
canonicalization does not broaden the domain: it replaces only already
completed upper residuals with the algebraic `fixed - beliefs` form when the
raw defect is within the lane tolerance, and retains both digests. Every arm
starts from one canonical `opaque_state_ref`.

Integrity and empirical success are separate. An incomplete matrix or an
invalid identity or digest fails the backend. A complete matrix with a negative
`~R`, RNG, reserve, or order-effect outcome is retained with
`validation_passed=false`. This avoids irreversibly losing a negative result
after a single-attempt admission is claimed.

### `QW-LC4-E` execution-freeze materialization

See [ADR-070](decisions/ADR-070-stage3b-qwake-lc4-e-execution-freeze-materialization_EN.md).

- PR #130 merged into `main` `67a084c0b970ad79ad0692442f660085a73b080a` and passed independent verification;
- immutable image `torch2pc-layerwise-thesis:0.1.0-qw-lc4-e-freeze-67a084c0b970` was built from that commit with identity `sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d`;
- the nine-file `execution-freeze-v1` package binds the image, backend, entrypoint, admission, and authorization;
- raw `image-build.log` bytes are preserved exactly and the single path is classified in `.gitattributes` as sealed binary evidence;
- the internal record enables the future one-shot entrypoint, but the branch-level execution gate remains closed;
- no lease, output root, engineering [evidence](glossary_EN.md#term-evidence), scientific execution, [test-dataset access](glossary_EN.md#term-test-dataset-access) to the test [dataset](glossary_EN.md#term-dataset), or publication exists.

### QW-LC4-E one-shot engineering invocation authorization

See [ADR-071](decisions/ADR-071-stage3b-qwake-lc4-e-one-shot-invocation-authorization_EN.md).

After verified merge of PR #131, a separate machine-readable authorization
package is materialized. It binds the exact immutable image,
`execution-freeze-v1`, admission, matrix authorization, backend, wrapper, and
entrypoint identities. The internal record authorizes one future engineering
invocation and one future lease claim.

Authorization is not execution. No lease, output root, or staging tree is
created on this branch; authorization is unconsumed and model code is not
invoked.

```text
qwake_adr=ADR-071-stage3b-qwake-lc4-e-one-shot-invocation-authorization
qwake_invocation_authorization_sha256=sha256:0a60dacc1bfd5073cf52d76f2ec33ae54f00899aad9877d44607199659fda75a
qwake_invocation_authorization_registry_sha256=sha256:9a47f79e9607db98a2c7c224c25cbeee920974d4c339eef4ef82d4f9aa7c8f83
ONE_SHOT_INVOCATION_AUTHORIZED=true
FUTURE_LEASE_CLAIM_AUTHORIZED=true
FUTURE_RUNTIME_EXECUTION_AUTHORIZED=true
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

### `QW-LC4-E` one-shot host invocation-wrapper authoring

See [ADR-072](decisions/ADR-072-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-authoring_EN.md).

After verified merge of PR #132, only the pure future host-wrapper contract is
materialized. It binds authorization to the exact immutable image and in-image
entrypoint, forbids project-source and dataset mounts, and limits a future
container to frozen packages, Torch2PC, and the results directory. The contract
also fixes `/dev/kfd` and `/dev/dri`, user/group and resource-input wiring, the
exact command template, and the `/tmp` tmpfs required by a read-only root
filesystem. Container invocation, local-image inspection, lease claim, and
execution remain absent.

```text
qwake_invocation_wrapper_contract_sha256=sha256:4c4cb163e8c2a33b0563cc3b9cb873a87acf8ea75bb3e807d157d51c5a4dd29b
INVOCATION_WRAPPER_CONTRACT_PRESENT=true
CONTAINER_COMMAND_TEMPLATE_PRESENT=true
GPU_DEVICE_BINDING_COUNT=2
TMPFS_REQUIRED=true
TMPFS_TARGET=/tmp
HOST_RUNTIME_INVOKER_PRESENT=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

### `QW-LC4-E` one-shot host invocation-wrapper implementation

ADR-073 adds fail-closed inspection of the exact local image and a deterministic
builder for the future `docker run` argv as data. The implementation compares
the full normalized image identity, requires canonical resource inputs, and
constructs exactly three mounts and two devices. It contains no host invoker,
creates no lease, and does not open `LOCAL_COMPUTE`
[execution](glossary_EN.md#term-execution).

### `QW-LC4-E` one-shot host-runtime-invoker authoring

See [ADR-074](decisions/ADR-074-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-authoring_EN.md).

- PR #134 merged into `main` `be6486a9e3670343132f2c863a5a0cd5969ee9f6` and passed independent verification;
- the pure contract binds exact image inspection and canonical argv implementation to one future spawn attempt;
- the host must recheck image, command, and effect absence immediately before spawn;
- only the container entrypoint may claim the execution lease, in the same process that invokes the backend;
- automatic retry is forbidden after spawn, and a claimed lease persists after every failure;
- the invoker, lease, output, [evidence](glossary_EN.md#term-evidence), test data, and publication remain absent.

### `QW-LC4-E` one-shot host-runtime-invoker implementation

See [ADR-075](decisions/ADR-075-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-implementation_EN.md).

- PR #135 merged into `main` `7f1655346bca77834d73a660c9857f1ff23b826c` and passed independent verification;
- double image and canonical-argv revalidation, one no-shell `Popen`, and a fixed host environment are implemented;
- the child receives a separate process group, `SIGINT`/`SIGTERM` forwarding, a terminal timeout, and bounded output;
- the host writes no lease and persists neither command nor logs;
- the verifier and tests never invoke Docker runtime, so execution and output remain absent.

### `QW-LC4-E` one-shot host-runtime-invoker repository freeze

See [ADR-076](decisions/ADR-076-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-repository-freeze_EN.md).

- PR #136 merged into `main` `da51c8d858c541372525125640db99062041fc20` and passed independent verification;
- the receipt binds both parents, both implementation commits, the 16-file tree, and corrected hashes;
- it records 2/2 CI checks, 139 targeted tests, and 1186 full tests;
- the implementation and exact `docker run` path exist, but the one-shot engineering invocation is not yet permitted;
- image inspection, `docker run`, lease claim, authorization consumption, output, and scientific capabilities remain absent;
- after receipt merge, the next atomic step is a separate one-shot operator operation.

### `QW-LC4-E` one-shot engineering invocation admission

See [ADR-077](decisions/ADR-077-stage3b-qwake-lc4-e-one-shot-engineering-invocation-admission_EN.md).

- the PR #137 repository freeze is complete on `main` `3454d12d3cc16c9c50977e2a598e2bc1a8768441`;
- the admission rebinds the authorization, image, Torch2PC revision, and executable host invoker;
- static identities are verified without image inspection or process spawn;
- the future operator operation must recheck image, resources, lease, output, and staging;
- branch permission, invocation, lease, output, and scientific capabilities remain closed.

### `QW-LC4-E` one-shot engineering invocation operation record

See [ADR-078](decisions/ADR-078-stage3b-qwake-lc4-e-one-shot-engineering-invocation-operation_EN.md).

- PR #138 merged into `main` `28be77706bc86abaf34f86e9bdcbdcb9cc2810a8` and passed independent verification;
- the operation record binds the admission merge commit, authorization, image, Torch2PC revision, and host invoker;
- it freezes 13 required host-resource keys, two image inspections, two canonical-argv materializations, and one allowed `Popen`;
- current-runtime verification has not occurred: `PREEXECUTION_IDENTITY_VERIFIED=false`;
- image inspection, command, lease, spawn, output, and scientific capabilities remain closed;
- after record merge, the next atomic step is a separate effectful execution operation.

### `QW-LC4-E` one-shot engineering invocation execution authorization

See [ADR-079](decisions/ADR-079-stage3b-qwake-lc4-e-one-shot-engineering-invocation-execution-authorization_EN.md).

- PR #139 was merged into `main` at `b0f6729e8fd1cb1aa172eef488dc56e36b335173` and independently verified;
- the authorization binds the operation merge, `operation-v1`, previous one-shot permission, image, Torch2PC revision, and host invoker;
- only one future pre-execution verification and one future engineering invocation are authorized after separate post-merge verification;
- verification must use the exact 13 host resources, two equal image inspections, two equal argv materializations, and at most one `Popen`;
- the authoring branch preserves `PREEXECUTION_IDENTITY_VERIFIED=false` and `ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false`;
- no image inspection, command materialization, lease, spawn, result, or scientific capability is present.

### Pre-execution contract for the `QW-LC4-E` one-shot engineering invocation

See [ADR-080](decisions/ADR-080-stage3b-qwake-lc4-e-one-shot-engineering-invocation-preexecution-verification_EN.md).

- PR #140 was merged into `main` as `49c4b97e93b47cefbf35576736927ece02c9402b` and independently verified;
- the contract binds the merged authorization to the exact host-invoker implementation;
- the future atomic operation must call `invoke_one_shot_host_runtime` exactly once;
- both image inspections, both canonical argv materializations, and the single child creation remain one continuous sequence;
- the static verifier does not call Docker and preserves `PREEXECUTION_IDENTITY_VERIFIED=false`;
- the lease, output, [evidence](glossary_EN.md#term-evidence), and actual [execution](glossary_EN.md#term-execution) remain absent.

`decision marker`: `ADR-080-stage3b-qwake-lc4-e-one-shot-engineering-invocation-preexecution-verification`.

## `QW-LC4-E`: bounded one-shot engineering invocation runtime operation

See [ADR-081](decisions/ADR-081-stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation_EN.md).

After independent verification of the PR #141 merge, a pure atomic-operation
contract and bounded entry point are materialized. It accepts exact host
resources, a claim time, two acknowledgements, and explicit permission, then
may delegate dynamic verification and launch exactly once to the previously
frozen host invoker. The verifier never calls the new entry point.

```text
qwake_adr=ADR-081-stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation
qwake_runtime_operation_base_commit=494e6a0b2f10c26b49c90fbb84c23565699a4064
qwake_runtime_operation_sha256=sha256:0332428014f7f8385c789ba7e7c55d6c2ec03b020e3f83df9ac9714483bb6bf8
PREEXECUTION_VERIFICATION_COMPLETE=true
RUNTIME_OPERATION_RECORD_PRESENT=true
RUNTIME_OPERATION_EXECUTOR_ENTRYPOINT_IMPLEMENTED=true
RUNTIME_OPERATION_STATIC_CONTRACT_VERIFIED=true
ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_OPEN=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

### `QW-LC4-E` runtime-operation identity repair

See [ADR-082](decisions/ADR-082-stage3b-qwake-lc4-e-runtime-operation-identity-repair_EN.md).

Historical ADR-081 and package v1 remain unchanged. A separate repair package
binds the corrected source tree to the PR #142 merge commit and requires the
runtime-operation verifier to check its own executable identity. The execution
request remains closed pending corrected validation, repair merge, persistent
lease v2, and a durable negative host outcome.

### `QW-LC4-E` persistent evidence chain v2

See [ADR-083](decisions/ADR-083-stage3b-qwake-lc4-e-persistent-evidence-chain-v2_EN.md).

After independent verification of the PR #143 merge, a separate authoring
package binds the current invocation authorization, execution authorization,
pre-execution, runtime-operation, and identity-repair identities to the exact
image, Torch2PC revision, output root, and `invocation_count=1`. Pure builders
define the future persistent lease v2 and mandatory terminal host-outcome
receipt, including prelaunch/spawn failure, nonzero return, timeout, and signal.
Atomic persistence, the lease-bound capability, and actual invocation remain
closed.

```text
qwake_adr=ADR-083-stage3b-qwake-lc4-e-persistent-evidence-chain-v2
qwake_persistent_evidence_chain_v2_sha256=sha256:c0a6195080cec64e6104a90076366cc2bfa10a723b45a7389cd77fa1b3b11bd1
CORRECTED_FULL_VALIDATION_RECEIPT_PRESENT=true
RUNTIME_OPERATION_IDENTITY_REPAIR_MERGED=true
LATEST_AUTHORIZATION_BOUND_IN_PERSISTENT_LEASE_TEMPLATE=true
DURABLE_NEGATIVE_HOST_OUTCOME_DEFINED=true
PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=false
DURABLE_OUTCOME_WRITER_IMPLEMENTED=false
LEASE_BOUND_HOST_INVOKER_ENFORCED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
RUNTIME_EXECUTION_PERFORMED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## `QW-LC4-E`: persistent evidence chain v2 implementation

ADR-084 implements exclusive persistence of the persistent lease v2 and durable
terminal host-outcome receipt. Persistence fails closed on any collision,
symbolic link, incomplete frozen identity, or mismatch in the exact lease
bytes. Durability uses mode `0600`, file `fsync`, no-replace hard-link
promotion, and parent-directory `fsync`. The implementation is not yet wired to
the host invoker; the real lease, outcome, image inspection, command
materialization, and execution remain absent.

## Lease-bound host invoker

ADR-085 adds the only prospective lease-bound entry point. It requires exact persisted lease-v2 bytes before image inspection or process creation and writes a durable terminal receipt with no retry after the claim. The historical direct operation remains only as frozen evidence and is superseded for future authorization. Execution stays closed.

## `QW-LC4-E`: final execution acknowledgement authoring

ADR-086 introduces the static contract for a future separate operator
acknowledgement after verified PR #146 was merged as
`2957d8f6975c88e7bdb23243e3915c7f51d4ba47`. The contract binds evidence chain
v2, persistent-writer implementation, the lease-bound invoker, image,
Torch2PC, output root, and `invocation_count=1`. Future issuance requires the
exact phrase `ACKNOWLEDGE_QWAKE_LC4_FINAL_ONE_SHOT_EXECUTION`, operator identity,
and a UTC time after merge. Authoring does not issue the acknowledgement,
materialize the lease, or perform invocation.

```text
wiring_pr=146
wiring_focused_tests=39
wiring_targeted_tests=240
wiring_full_tests=1287
wiring_full_test_warnings=14
FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```


## `QW-LC4-E`: final acknowledgement issuance authoring

ADR-087 binds the verified PR #147 merge and exact ADR-086 package to the sole
future acknowledgement file. The contract requires separate operator and issuer
identities, ordered timestamps, canonical JSON, atomic no-overwrite persistence,
mode `0600`, `fsync`, and exact persisted-byte reverification. Writer
implementation, acknowledgement, lease, and invocation remain absent.

```text
acknowledgement_authoring_pr=147
acknowledgement_authoring_focused_tests=50
acknowledgement_authoring_targeted_tests=251
acknowledgement_authoring_full_tests=1298
acknowledgement_authoring_full_test_warnings=14
ACKNOWLEDGEMENT_ISSUANCE_CONTRACT_AUTHORED=true
ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTED=false
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```


## `QW-LC4-E`: final acknowledgement writer implementation

ADR-088 implements atomic persistence of an already-verified acknowledgement
envelope to the sole ADR-087 path. It uses `O_EXCL`, a no-overwrite hard link,
mode `0600`, `fsync`, symbolic-parent rejection, stale-temporary rejection, and
exact-byte reverification. No production callsite exists, so merging the
implementation neither creates an acknowledgement nor opens invocation.

```text
issuance_authoring_pr=148
issuance_authoring_focused_tests=61
issuance_authoring_targeted_tests=262
issuance_authoring_full_tests=1309
issuance_authoring_full_test_warnings=14
ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```


### Final acknowledgement materialization authoring

After the writer implementation merge, a separate static slice binds future
materialization to the exact operator, issuer, materializer, ordered UTC times,
target path, and canonical-envelope SHA-256. The writer is not called; the
acknowledgement, lease, and local compute remain absent.


### Final acknowledgement materialization implementation

ADR-090 adds a materializer whose import is effect free. Only a separate
explicit call can pass the exact prospective materialization to the existing
atomic writer and then reverify the persisted bytes. No call occurs in the
current slice; the acknowledgement, lease, and local compute remain absent.

### Final-acknowledgement materializer invocation authoring

ADR-091 separates the pure invocation contract from the adapter implementation
and the actual materialization. The future adapter may call only the exact
materializer and may not call the writer directly. Automatic and blind retry are
forbidden: an uncertain outcome must first inspect the durable target. An absent
target permits only a newly and explicitly authorized attempt, a valid existing
target is treated as success without another call, and an invalid target fails
closed. The materializer is not called in this slice.

### Final-acknowledgement materialization invocation implementation

ADR-092 implements a library adapter without a production callsite. It probes
the exact target before the materializer: absence permits one call, a valid
existing target is successful recovery without another call, and an invalid
target fails closed. Automatic and blind retry are absent.

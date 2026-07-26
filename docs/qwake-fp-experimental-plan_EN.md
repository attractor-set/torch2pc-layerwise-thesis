# Bounded `QWake-FP` validation plan

[Русская версия](qwake-fp-experimental-plan.md)

**Status:** active plan after `QW-4B-DOC-R1`; [execution](glossary_EN.md#term-execution),
new oracle-label creation, confirmatory/test access, and policy activation are
closed.

## 1. Central object

`QWake-FP` is a bounded shadow instantiation of `QWake-PC` for the registered
case:

```text
algorithm=FixedPred
eta=1
canonical_executor=stage2_baseline
architecture=lenet_classic
validation_mode=shadow_only
independent_unit=model_seed
```

General `QWake-PC` transferability is not established.

## 2. Research model

For action `a` in state `s`, consider `R(a,s)`, `M(a)`, `Γ(a,s)`, and `C(a,s)`
separately. The required response determines neither one mechanism nor one cost.
Method comparison therefore separates equivalence in `R` from equivalence in
`C`.

Only actions whose registered [decision regret](glossary_EN.md#term-decision-regret)
does not exceed `ε` are admissible. Among them, select the action with minimum
registered cost or apply a preregistered Pareto rule.

## 3. Two development boundaries

### `QW-4B` [baseline](glossary_EN.md#term-baseline) validation

It establishes that observation levels `A0/A1/A2` do not interfere with
[baseline](glossary_EN.md#term-baseline) `FixedPred`, are measured correctly on CPU and ROCm, and can be sealed
in one engineering report. Baseline validation does not contain
`LOCAL_COMPUTE`.

The three matched pairs remain unchanged:

```text
P0: B0 <-> B0+A0
P1: B0 <-> B0+A0+A1
P2: B0 <-> B0+A0+A1+A2
```

### The `QW-LC` extension

Only after a sealed baseline report, it adds:

```text
LOCAL_COMPUTE
├── LOCAL_SWEEP
└── ANALYTIC_COMPLETION
```

The first analytic [candidate](glossary_EN.md#term-candidate) is restricted to
`fixedpred_eta1_wavefront_completion_v1` and does not generalize to `Strict`,
arbitrary `eta`, or arbitrary computational graphs.

## 4. Permission model

Capability presence in an image does not authorize its use:

```text
capability_present != capability_permitted
```

Every effectful function must check its own permission. A disabled capability
does not register a hook, read a tensor, allocate device memory, synchronize the
device, or create output.

Required permission classes:

```text
COLLECT_A0
COLLECT_A1
COLLECT_A2
COMPUTE_CANONICAL_SUFFIX
COMPUTE_POST_ACTION_ORACLE
EXECUTE_LOCAL_SWEEP
EXECUTE_ANALYTIC_COMPLETION
RUN_COST_DOMINANCE_CHECK
ACCESS_DESIGN_DATA
ACCESS_CALIBRATION_DATA
ACCESS_CONFIRMATORY_DATA
ACCESS_REPLICATION_DATA
SELECT_POLICY
FREEZE_POLICY
EXECUTE_SHADOW_POLICY
SEAL_EVIDENCE
PUBLISH_RESULTS
```

## 5. Campaign roles

### `C1`

Collects complete trajectories, `A0/A1/A2`, registered analytics, transition
cost, canonical suffix, and post-action labels. Policy selection and
confirmatory access are forbidden.

### `C2`

Operates only offline on sealed `C1` artifacts. New model execution, tensors,
and labels are forbidden. Its output is one frozen shadow policy or a bounded
negative result.

```text
c2_execution_mode=offline_only
c2_input_artifacts=sealed_c1_trajectory_dataset
c2_live_fixedpred_execution_permitted=false
c2_new_observation_collection_permitted=false
c2_new_oracle_generation_permitted=false
c2_policy_selection_from_frozen_artifacts_only=true
C2_ALLOWED=ACCESS_SEALED_C1_ARTIFACTS,RUN_OFFLINE_REPLAY
C2_FORBIDDEN=EXECUTE_FIXEDPRED,COMPUTE_NEW_ORACLE_LABELS
```

### `C3`

Uses untouched model seeds, loads the frozen policy, and always completes the
canonical suffix for post-action audit. Evaluation order is safety, coverage,
and net cost.

### `R`

Repeats `C3` without retuning. Only the preregistered replication [configuration](glossary_EN.md#term-configuration)
changes.

## 6. Receipt chain

```text
QW-4B-F-v2 receipt -> QW-4B-E-v2
QW-4B-E-v2 report -> QW-LC0
QW-LC4-E report -> QW-5
QW-5 image receipt -> C1
C1 receipt -> C2
C2 policy receipt -> C3
C3 evidence receipt -> R
C3/R evidence -> publication gate
```

Each next request binds the source commit, image digest, role, data partition,
model-seed set, and preceding receipts.

## 7. Implementation sequence

### `QW-0`–`QW-4B-I`

Historically completed: scope freeze, pure contract, special case,
backend-neutral pipeline, `QW-4A` request, and `QW-4B-I` baseline-validation
implementation.

```text
historical_sequence=QW-2->QW-3->QW-4A->QW-4B-I
qwake_fp_special_case_contract_id=stage3b-qwake-fp-special-case-v1
qwake_fp_superset_pipeline_implemented=true
qwake_fp_superset_pipeline_execution_open=false
qwake_fp_live_adapters_bound=false
qwake_fp_component_registry_closed=true
qwake_fp_offline_replay_implemented=true
```

### `QW-4B-DOC-R1`

Fully synchronize active documentation, research logs, the machine-readable
contract, and boundary tests. Retire the old authorization. A new image is
mandatory after merge.

### New baseline image

Build an immutable image from the commit after `QW-4B-DOC-R1` merge. The image
still contains no `LOCAL_COMPUTE` implementation; it supports a clean repeat of
baseline validation.

### `QW-4B-F-v2`

Refreeze the preflight, static-validation receipt, exact CPU/ROCm cells, new
image digest, new source commit, output root, and single-[attempt](glossary_EN.md#term-attempt) authorization.

### `QW-4B-E-v2`

Execute the six baseline cells once and seal the two-lane engineering report.
`QW-LC0` remains closed if this step fails.

### `QW-LC0`

Freeze `R/M/Γ/C` semantics, candidate scope, claim boundaries, and the ban on
universal generalization.

### `QW-LC1`

Freeze the final response and mandatory observables reproduced by every
mechanism.

### `QW-LC2`

Freeze measured `Γ` and its non-duplicating map into `C`.

### `QW-LC3`

Define matched shadow validation of `LOCAL_SWEEP` and
[analytic completion](glossary_EN.md#term-analytic-completion) with shared state,
RNG restoration, and a complete exact-reserve suffix.

### `QW-LC4-I`

Implement the bounded candidate without opening execution.

### `QW-LC4-F`

Build a new extension image and issue a separate single-attempt authorization.

### `QW-LC4-E`

Execute extension engineering validation and seal its report. Only a successful
report opens `QW-5`.

### `QW-5`

Freeze the single scientific image for `C1/C2/C3/R`. Code and dependencies do
not change after this point.

### `C1` → `C2` → `C3` → `R`

Run collection, offline selection, confirmatory shadow evaluation, and
replication without retuning in sequence.

## 8. Baselines and ablations

The minimum set includes the complete canonical suffix, `LOCAL_SWEEP`,
`ANALYTIC_COMPLETION`, and a safe exact reserve, nested `A0`, `A0+A1`, `A0+A1+A2`
representations, and registered analytics. Observation, control, and exact-reserve
costs are accounted for separately.

## 9. Publication strength

A positive result requires bounded decision regret, zero dangerous misses,
nonzero coverage, and positive net saving together. A later gain cannot offset
an earlier failure. Negative findings are preserved without changing criteria.

## 10. Outside mandatory scope

A universal symbolic solver, arbitrary architectures, arbitrary `eta`, active
control before shadow validation, confirmatory retuning, and test-data use for
mechanism or policy selection remain outside scope.

## 11. Current closed boundary

```text
qwake_documentation_refactor_complete=true
qwake_old_runtime_authorization_retired=true
qwake_old_runtime_authorization_reuse_permitted=false
qwake_new_image_required=true
qwake_new_runtime_preflight_captured=false
qwake_new_runtime_authorization_issued=false
qwake_runtime_execution_performed=false
qwake_runtime_validation_performed=false
qwake_engineering_evidence_present=false
qwake_fp_execution_permitted=false
qwake_local_compute_contract_frozen=true
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
qwake_scientific_image_freeze_permitted=false
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
publication_permitted=false
full_stage3b_campaign_complete=false
```


## 12. Current `QW-LC0` state

Semantics and scope are materialized as `stage3b-qwake-lc0-semantics-scope-v1`. The exact response and
`~R` operator remain for `QW-LC1`; measured `Γ`, the `Φ` map, and `~C` remain for
`QW-LC2`. The next slice does not open before this freeze is merged.

```text
qwake_qw_lc0_semantics_scope_frozen=true
qwake_qw_lc1_transition_permitted=false
qwake_qw_lc1_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
scientific_execution_open=false
publication_permitted=false
```
## 13. Normative `QW-LC1` schema

`stage3b-qwake-lc1-required-response-schema-v1` turns the short `QW-LC1` description into an exact contract.
Response components are compared by separate registered entries, so an error in
a small parameter or layer cannot be hidden by a global norm. Structural
mismatch, a missing entry, a non-finite value, or a one-zero case fails
immediately.

Threshold profiles:

| Profile | `max_abs` | `max_relative_l2` | `min_cosine` | `zero_atol` |
|---|---:|---:|---:|---:|
| `cpu_float64_engineering` | `1e-9` | `1e-7` | `0.99999` | `1e-12` |
| `rocm_float32_canonical` | `1e-5` | `1e-3` | `0.999` | `1e-7` |

ROCm/float32 remains decision-facing. CPU/float64 is an engineering control.
Neither profile establishes actual equivalence before future matched
validation.

# Bounded `QWake-FP` validation plan

[Русская версия](qwake-fp-experimental-plan.md)

**Status:** docs-only plan freeze under `ADR-042`; [execution](glossary_EN.md#term-execution), feature
collection, oracle labels, calibration, confirmatory access, and the test split
remain closed.

## 1. Central object

General `QWake-PC` defines state, action, admission, cost, provenance, and
[fallback](glossary_EN.md#term-fallback) classes. The master's thesis implements and validates only
[QWake-FP](glossary_EN.md#term-qwake-fp), one deterministic shadow instantiation for the corrected Rosenbaum
special case:

```text
algorithm=FixedPred
eta=1
canonical_executor=stage2_baseline
validation_mode=shadow_only
full_reference=depth_bounded_canonical_suffix
independent_unit=model_seed
```

Experimental conclusions apply only to this registered instantiation. General
transfer of `QWake-PC` is not treated as validated.

## 2. Central question

> Can a frozen `QWake-FP` use cheap pre-action information to safely recognize
> a task-relative sufficient partial `FixedPred` prefix before the full
> canonical suffix and retain positive end-to-end savings after observation,
> analytic, synchronization, control, trace, and fallback cost?

The question is decomposed into four ordered gates:

1. do pre-terminal sufficient states exist;
2. are they recognizable from admissible pre-action data;
3. does frozen admission pass the safety limit;
4. do positive net savings remain?

A later interpretation is forbidden unless the preceding gate passes.

## 3. Single superset image

Before scientific execution, one finite pipeline is implemented with:

- canonical `FixedPred` executor;
- QWake state machine;
- A0 / A1 / A2 collectors;
- finite analytic registry;
- canonical suffix and post-action O;
- edge measurement and decision-cost mapping;
- opportunity and recognizability analysis;
- policy-manifest interpreter;
- baselines and nested ablations;
- shadow confirmatory and replication evaluators;
- sealing and publication export.

Pre-freeze validation binds:

```text
SOURCE_COMMIT
SOURCE_TREE_HASH
IMAGE_DIGEST
TORCH2PC_COMMIT
CODE_MANIFEST_SHA256
OUTPUT_SCHEMA_VERSION
CAPABILITY_SCHEMA_VERSION
POLICY_SCHEMA_VERSION
```

Executable code and dependencies do not change between C1, C2, C3, and R.

## 4. Permission model

A capability may be present in the image without being executable:

```text
capability_present != capability_permitted
```

The mandatory registry covers:

```text
COLLECT_A0
COLLECT_A1
COLLECT_A2
RUN_ANALYTIC_EXACT
RUN_ANALYTIC_CONSERVATIVE
RUN_ANALYTIC_HEURISTIC
RUN_COST_DOMINANCE_CHECK
COMPUTE_CANONICAL_SUFFIX
COMPUTE_POST_ACTION_ORACLE
ACCESS_DESIGN_DATA
ACCESS_CALIBRATION_DATA
ACCESS_CONFIRMATORY_DATA
ACCESS_REPLICATION_DATA
RUN_OPPORTUNITY_ANALYSIS
RUN_RECOGNIZABILITY_ANALYSIS
SELECT_POLICY
FREEZE_POLICY
LOAD_FROZEN_POLICY
EXECUTE_SHADOW_POLICY
EVALUATE_CONFIRMATORY
EVALUATE_REPLICATION
SEAL_EVIDENCE
PUBLISH_RESULTS
```

Every effectful function performs its own permission check. A disabled
capability registers no hook, reads no tensor, allocates no memory,
synchronizes no device, and creates no output.

A manifest does not carry code. It may select only registered roles,
capabilities, and entrypoints.

## 5. Campaign roles

### `C1_COLLECTION`

Permits trajectory collection, A0/A1/A2, registered analytics, full suffix,
post-action oracle, edge costs, opportunity analysis, and sealing.

Forbids policy selection, confirmatory access, shadow policy execution, and
publication.

Outputs:

- complete trajectory benchmark;
- oracle sufficiency labels;
- remaining-suffix cost;
- opportunity map;
- sealed C1 receipt.

### `C2_CALIBRATION`

C2 is a strictly offline stage. It reads only sealed C1 trajectory artifacts;
model execution and collection of new observations are not permitted.

It permits `ACCESS_SEALED_C1_ARTIFACTS`, `RUN_OFFLINE_REPLAY`,
`RUN_RECOGNIZABILITY_ANALYSIS`, [baseline](glossary_EN.md#term-baseline) evaluation through
`EVALUATE_BASELINES`, `SELECT_POLICY`,
`FREEZE_POLICY`, and `SEAL_EVIDENCE`.

It forbids `EXECUTE_FIXEDPRED`, `COLLECT_A0`, `COLLECT_A1`, `COLLECT_A2`,
`RUN_LIVE_ANALYTICS`, `COMPUTE_CANONICAL_SUFFIX`, `COMPUTE_NEW_ORACLE_LABELS`,
`ACCESS_CONFIRMATORY_DATA`, changes to the collector/oracle/cost mapping, and
publication.

Offline replay opens only the already stored field for the next observation
level or analytic step, reproduces the policy transition, and adds the marginal
cost measured in C1. It creates no new tensor value and recomputes no oracle.

Outputs:

- risk/coverage/cost frontier;
- nested representation ablations;
- one frozen QWake-FP policy;
- `POLICY_MANIFEST_SHA256`;
- sealed C2 receipt.

### `C3_CONFIRMATORY`

Permits the untouched confirmatory partition, loading the frozen policy, shadow
execution, full suffix, post-action audit, confirmatory evaluation, and
sealing.

Forbids policy selection/freeze and changes to thresholds, features, analytic
order, primary defect, baselines, or cost mapping.

Result order:

```text
SAFETY -> COVERAGE -> NET_COST
```

### `R_REPLICATION`

Uses the same image digest, policy manifest, thresholds, analytic order, and
cost mapping. Only a preregistered replication [configuration](glossary_EN.md#term-configuration) changes. The
preferred setting is MNIST with the same [architecture](glossary_EN.md#term-architecture). Retuning is forbidden.

## 6. Sealed receipt chain

```text
C1 receipt -> authorizes C2
C2 policy-freeze receipt -> authorizes C3
C3 evidence receipt -> authorizes R and result synthesis
C3/R sealed evidence -> separate publication gate
```

Every request binds image digest, source identity, code manifest, role,
partition, seed set, policy hash, and prior-stage receipts.

## 7. Implementation stages

### `QW-0` — scope freeze

Freeze the [QWake-PC](glossary_EN.md#term-qwake-pc) / [QWake-FP](glossary_EN.md#term-qwake-fp) distinction, special case, C1/C2/C3/R roles,
single image, and publication-strength package. Documentation only.

### `QW-1` — pure QWake contract

Implement without Torch2PC/GPU:

```text
FrontierState
ObservationSnapshot
AnalyticResult
FrontierAction
AdmissionProposal
AdmissionDecision
EdgeMeasurement
DecisionCost
OracleLabel
Provenance
Capability
CampaignRole
PermissionSet
ExecutionContext
```

Gate: deterministic replay, fail-closed defaults, invalid-combination
rejection, and property tests.

### `QW-2` — QWake-FP special-case contract

Freeze executor, eta=1, architecture, horizon, snapshot boundaries, response,
primary defect, observation levels, analytic registry, cost schema, baselines,
roles, and receipt requirements.

Status: completed by [ADR-043](decisions/ADR-043-stage3b-qwake-fp-special-case-contract_EN.md)
and the sealed `stage3b-qwake-fp-special-case-v1`. The contract freezes exact
A0/A1/A2, three analytics, B0-B7, P0-P2, and non-duplicating cost mapping;
execution remains closed and the next stage is `QW-3`.

### `QW-3` — superset pipeline implementation

Status: the backend-neutral mandatory pipeline is implemented. It includes a
closed component registry, effect-local planning, an immutable trajectory
schema, exact `A0/A1/A2`, a finite policy interpreter, B0-B7 and nested
ablations, cost mapping, opportunity/recognizability, shadow/replication
evaluation, pure sealing, and `rendered_not_published` export. Policy remains
data for the embedded interpreter; arbitrary code/plugins are absent. Live
Torch2PC/ROCm adapters are not bound, execution remains closed, and the next
stage is `QW-4`.

```text
qwake_fp_superset_pipeline_implemented=true
qwake_fp_superset_pipeline_execution_open=false
qwake_fp_live_adapters_bound=false
qwake_fp_component_registry_closed=true
qwake_fp_offline_replay_implemented=true
qwake_fp_next_stage=QW-4
```

### `QW-4` — pre-freeze validation

Run static/unit/integration checks, CPU/ROCm smoke, permission matrix, negative
permission tests, deterministic replay, schema checks, corrupt/missing-manifest
tests, receipt-chain tests, and baseline replay tests.

Validate observation through three matched pairs over one logical B0 definition
and a separate matched reference execution inside each pair:

```text
P0: B0 <-> B0+A0
P1: B0 <-> B0+A0+A1
P2: B0 <-> B0+A0+A1+A2
```

Each pair checks canonical-result/RNG/transition equivalence, observation
correctness, and accumulated cost. Also verify A0/A1 nesting, non-execution of
disabled capabilities, post-action oracle isolation, and registered-analytic
non-interference.

### `QW-5` — single image freeze

Freeze one code/environment identity. Any material error after freeze requires
a new digest and protocol version; old [evidence](glossary_EN.md#term-evidence) is not rewritten.

### `QW-6` — C1 collection and opportunity

Collect complete design/calibration trajectories sufficient for later offline
C2: every snapshot, A0/A1/A2, registered analytics, marginal edge costs, the
canonical suffix, and post-action oracle labels. Test:

```text
exists_preterminal_sufficient_state
potential_avoided_cost_exceeds_lower_bound_of_control_overhead
```

If this gate fails, policy selection is not mandatory; the outcome is reported
as a bounded negative finding.

### `QW-7` — C2 offline recognizability, deterministic replay, and policy freeze

Without any new FixedPred execution, replay from sealed C1 artifacts:

```text
A0
A0+A1
A0+A1+A2
A0+A1+A2+analytics
```

Select the simplest safe nearly non-dominated policy. Safety has lexicographic
priority over coverage and cost.

### `QW-8` — C3 untouched confirmatory shadow evaluation

The primary unit is [model seed](glossary_EN.md#term-model-seed). Snapshot-level rows are nested diagnostics only.
After partition opening, policy and analysis contracts do not change.

Allowed outcome classes:

```text
SAFE_AND_BENEFICIAL
SAFE_BUT_NOT_BENEFICIAL
UNSAFE
NO_NONTRIVIAL_COVERAGE
INSUFFICIENT_EVIDENCE
```

### `QW-9` — replication without retuning

Apply the same frozen policy to a preregistered additional setting. Success
strengthens external validity; failure identifies a transfer boundary.

### `QW-10` — synthesis and publication gate

Combine existence, recognizability, safety, coverage, cost, ablations, and
replication. Publication requires a separate bounded decision after sealing.

## 8. Baselines and ablations

Mandatory baselines are embedded before image freeze:

```text
B0 full canonical suffix
B1 fixed prefix
B2 residual/prediction-error threshold
B3 A0-only
B4 fixed A0->A1->A2 cascade
B5 fixed analytic registry
B6 frozen QWake-FP
B7 post-action oracle frontier
```

B7 is an offline upper bound only. No baseline is added after confirmatory
access.

Mandatory ablations independently remove:

- A1;
- A2;
- analytic steps;
- adaptive ordering;
- cost-dominance checks.

## 9. Publication strength

The minimum publication-strength package includes:

- strong simple baselines;
- untouched confirmatory seeds;
- exact one-sided seed-level safety bounds;
- one replication without retuning;
- complete observer/control overhead accounting;
- a releasable trajectory benchmark with provenance;
- a positive or preregistered negative result.

## 10. Outside mandatory scope

```text
Strict
arbitrary eta
recursive multiscale control
spatial active sweeps
learned policy
contextual bandit
online exploration
cross-algorithm transfer
plugin or arbitrary policy DSL
QWake-SPC
```

These directions do not block master's completion and are not included in the
single mandatory image.

## 11. Current closed boundary

```text
qwake_fp_scope_freeze_complete=true
qwake_fp_execution_permitted=false
single_immutable_superset_image_frozen=false
c2_execution_mode=offline_only
c2_input_artifacts=sealed_c1_trajectory_dataset
c2_live_fixedpred_execution_permitted=false
c2_new_observation_collection_permitted=false
c2_new_oracle_generation_permitted=false
c2_policy_selection_from_frozen_artifacts_only=true
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

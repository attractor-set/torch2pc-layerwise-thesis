# Roadmap

[Русская версия](ROADMAP.md)

The roadmap separates completed, permitted, and blocked work. Every transition
requires verified artifacts, preserved claim boundaries, and a separate
admission decision.

## Stages 1–10 — complete

Infrastructure and pilot work, Stage 1/2, Stage 3A, Stage 3B B0 evidence, and
B0 statistical and engineering analysis are complete. The test dataset
remained closed.

## Stage 11 — Scenario A and initial theory — complete

`ADR-012` froze PC-TREF Balanced Core, PC-CATM, and Scenario A. `ECZ` has the
single meaning `Error-Cancellation Zone`; B0 remains an immutable baseline.

## Stage 12 — validity controls and `SI-MA0` — complete

Shortcut/equivalence controls, observer non-interference, deterministic
mechanism controls, and `SI-MA0` are complete. `REC`, `OBS`, `VER`, and `CMP`
passed, while `COST` failed; the negative global outcome is retained.

## Stage 13 — `SI-MA1` — complete

`SI-MA1` preregistration, implementation, confirmatory execution, and final
decision are complete. Across ten `model_seed` values and 180 matched blocks,
`CAL-COST-MA1=true` and `SI-MA1=pass`. The `SI-MA0` result remains unchanged,
and the cost of a future `ECZ` evaluator is excluded.

## Stage 14 — theoretical freeze before B1/B2 — complete

Operational PC-TREF/PC-CATM semantics, regret, norm contracts,
`precision-masked zero`, the cost vector, and cost separation are published
under `ADR-013`.

## Stage 15 — B1/B2 preregistration — complete

B1 `isolated_layer_vjp`, B2 `composite_vjp`, the shared overview, and
`ADR-014` are frozen. Publication tag: `stage3b-b1-b2-prereg-v1`. B2
`block`/`chunk` variants are outside this contract and require separate
preregistration.

## Stage 16 — exact candidates and [matched profiling](docs/glossary_EN.md#term-matched-profiling) — analysis published and receipt frozen

Complete:

- B1 is implemented and sealed as confirmatory `EQ-B1` over 120/120 pairs;
- B2 is implemented and passed engineering smoke over 12/12 triples and 24/24
  comparisons;
- the candidate-aware matched-profiling runner is implemented;
- the fail-closed confirmatory-B2 requirement before production launch is
  frozen;
- confirmatory B2 is preregistered for 120 triples and 240 comparisons;
- confirmatory B2 is executed and sealed: 120/120 triples, 240/240 comparisons, `EQ-B2-CONFIRMATORY=pass`, and derived `EQ-B2`; evidence is preserved as `stage3b-b2-confirmatory-63885e5-v1`.

Current boundary:

```text
scientific_admission=open
candidate_aware_runner=complete
b2_confirmatory_decision=pass_sealed
b2_confirmatory_request_frozen=true
b2_confirmatory_admission=present
matched_profiling_request_refrozen=true
matched_profiling_request_refresh_required=false
matched_profiling_execution_open=false
matched_profiling_execution_complete=true
matched_profiling_runtime_validation=valid
matched_profiling_evidence=sealed
matched_profiling_analysis_protocol_frozen=true
matched_profiling_analysis_implementation_complete=true
matched_profiling_analysis_preexecution_hardening=complete
matched_profiling_analysis_execution_request_frozen=true
matched_profiling_analysis_runtime_preflight_implementation=complete
matched_profiling_analysis_runtime_preflight_frozen=true
matched_profiling_analysis_execution_authorization_present=true
matched_profiling_analysis_synthetic_validation=pass
matched_profiling_analysis_execution_open=false
matched_profiling_analysis_execution_complete=true
matched_profiling_analysis_results_present=true
matched_profiling_analysis_output_audited=true
matched_profiling_analysis_output_seal_frozen=true
matched_profiling_analysis_output_evidence=true
matched_profiling_analysis_publication_gate_frozen=true
matched_profiling_analysis_publication_action_complete=true
matched_profiling_analysis_publication_receipt_frozen=true
matched_profiling_analysis_open=false
runtime_authorization=issued_consumed
measurements_allowed=false
results_publication_permitted=true
release_draft_required=false
release_publication_permitted=true
release_publication_complete=true
ex_if0_protocol_frozen=true
ex_if0_opened=true
ex_if0_complete=true
exact_implementation_frozen=true
exact_implementation_candidate=stage2_baseline
minimum_sufficient_sweep_rule_frozen=true
ex_if0_execution_permitted=false
oracle_label_generation_open=false
feature_collection_permitted=false
a11_off0_execution_open=false
recursive_aggregate_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

Execution request `v1`, runtime preflight, and authorization were frozen before
computation. The single read-only attempt completed on verified `main`; the
18-file output, receipt, and independent audit are preserved without rerunning.
An external seal binds those artifacts and moves the unchanged output into
repository evidence without rewriting generated metadata.

Stage 16 is complete: the fail-closed publication action succeeded, and the
exact remote receipt/status is frozen without rerunning the analysis.
Superiority claims, policy activation, and test access remain closed. Negative
and mixed results are retained.

## Stage 17 — `EX-IF0` and current design boundary — complete

`stage2_baseline` is frozen as the canonical exact reference and fail-closed
fallback. The decision epoch, task-relative endpoint, oracle margin, and
full-suffix rule for the minimum stably sufficient sweep are frozen. Execution
and oracle-label generation remain closed.

ADR-039–ADR-041 define D/U/S and the integrated temporal frontier. ADR-042
further bounds mandatory validation to one
[QWake-FP](docs/glossary_EN.md#term-qwake-fp) implementation for corrected
Rosenbaum FixedPred at `eta=1` and introduces one immutable permission-gated
image.

The historical policy queue after `EX-IF0` remains as provenance rather than
as the current mandatory critical path: `A11-OFF0` denotes offline opportunity
and recognizability analysis, `A11-OFF1` freezes the selected `predictor`, and
only then may `shadow` evaluation proceed. ADR-042 maps this work onto the
`C1/C2/C3` roles without opening execution gates.

## Stage 18 — `QW-0`: scope freeze — current docs-only stage

Freeze:

- general `QWake-PC` versus concrete `QWake-FP`;
- the corrected Rosenbaum FixedPred special case;
- `C1_COLLECTION / C2_CALIBRATION / C3_CONFIRMATORY / R_REPLICATION` roles;
- one finite superset image;
- permission checks at effect boundaries;
- frozen policy as a data manifest;
- publication-strength baselines, untouched seeds, ablations, replication, and
  a trajectory benchmark.

Scientific execution, labels, features, calibration, and test access remain
closed.

## Stage 19 — `QW-1`: pure QWake contract

Without Torch2PC or GPU, implement pure types for frontier state, observations,
analytics, actions, admission, costs, oracle labels, and provenance, plus
`Capability`, [campaign role](docs/glossary_EN.md#term-campaign-role),
`PermissionSet`, and `ExecutionContext`.

Gate: fail-closed defaults, deterministic replay, property tests, and rejection
of every incompatible permission combination.

Status: `QW-1` is implemented as a pure Python contract without Torch2PC/GPU;
all permissions default to deny, while role/receipt/digest bindings and
deterministic transitions are covered by exhaustive unit/property guards.
Scientific execution is not opened. The next mandatory stage is `QW-2`.

## Stage 20 — `QW-2`: QWake-FP special-case contract

Freeze FixedPred, eta=1, stage2_baseline, architecture, horizon, snapshot
boundaries, task-relative response, primary defect, A0/A1/A2, analytic
registry, cost schema, baselines, role matrix, and receipt requirements.

Status: `QW-2` is complete. `ADR-043`, the pure Python specification, and the
sealed `stage3b-qwake-fp-special-case-v1/contract.json` freeze `lenet_classic`,
the EX-IF0 defect, exact A0/A1/A2, analytic, B0-B7, and P0-P2 registries,
while permission/receipt mapping is inherited from `QW-1`. Execution remains
closed. The next mandatory stage is `QW-3`.

## Stage 21 — `QW-3`: superset pipeline implementation

Status: the backend-neutral mandatory contour is implemented in
`stage3b_qwake_fp_pipeline.py`. It provides a closed component registry,
effect-local planning, the exact `A0/A1/A2` trajectory schema, a finite policy
interpreter, B0-B7 and nested-ablation replay, cost mapping, opportunity and
recognizability, shadow/replication evaluation, pure sealing, and
`rendered_not_published` export. A manifest cannot load arbitrary code and may
activate only embedded capabilities.

Live Torch2PC/ROCm adapters are not bound, so execution remains closed. The
next mandatory stage is `QW-4`.

```text
qwake_fp_superset_pipeline_implemented=true
qwake_fp_superset_pipeline_execution_open=false
qwake_fp_live_adapters_bound=false
qwake_fp_component_registry_closed=true
qwake_fp_offline_replay_implemented=true
qwake_fp_next_stage=QW-4
```

## Stage 22 — `QW-4B-DOC-R1`: active-documentation refactor

Status: complete. The old authorization candidate was retired before execution, and active documents were moved to one `R/M/Γ/C` model, the `LOCAL_COMPUTE` family, and one stage sequence. The refactor was merged into `main` commit `e413bb1e13cee42f702512e499f994e90df21e45`.

## Stage 23 — `QW-4B-F-v2`: baseline-validation refreeze

Status: complete without model execution. The new immutable image, Torch2PC, preflight, receipt for 17 static checks, six `CPU/ROCm × P0/P1/P2` cells, absent output root, and one permitted attempt are frozen in the new package.

```text
source_commit=e413bb1e13cee42f702512e499f994e90df21e45
image_digest=sha256:bd91fab26df5f91a3aba90b8cad38badccab3a1a7bfb20efe4126a88a13236c4
preflight_sha256=sha256:79ead4a0e757272c788acd90700d61c0e5a0509fe64168f83f47dc0963ce4d00
authorization_sha256=sha256:d22063efa0c458c2498577139fa322b952081d8356cd1a6511f25188b12206b6
P0: B0 <-> B0+A0
P1: B0 <-> B0+A0+A1
P2: B0 <-> B0+A0+A1+A2
runtime_execution_performed=false
engineering_evidence_present=false
next_slice=QW-4B-E-v2
```

The single attempt has not been consumed. The next separate stage is `QW-4B-E-v2`.

## Stage 24 — `QW-4B-E-v2`: sealed baseline report

Status: complete. Repository seal commit
`26bc0ef635e13dba719d3356fe17382f0037d1df` was merged into `main`
`4f23b752a40ae05de9fc7ee49c9962c44083b71d` and reverified. The single attempt is permanently
consumed; retry is prohibited.

```text
runner_status=0
authorized_cell_count=6
cpu_lane_passed=true
rocm_lane_passed=true
runtime_execution_performed=true
engineering_evidence_present=true
image_freeze_eligible=true
scientific_evidence=false
publication_permitted=false
repository_evidence_sealed=true
post_merge_verification_passed=true
qw_lc0_transition_permitted=true
qw_lc0_open=true
qw_lc0_semantics_scope_frozen=false
next_slice=QW-LC0
post_lc0_next_slice=QW-LC1
```

The original wrapper failure, two failed recovery audits, successful recovery-v3,
and exact six-file output are preserved together. `QW-LC0` does not execute the
model; it must separately freeze only the extension semantics and scope.

## Stages 25–31 — the `QW-LC` extension

```text
QW-LC0  semantics and scope freeze
QW-LC1  required-response freeze
QW-LC2  resource-trajectory and cost freeze
QW-LC3  matched-validation freeze
QW-LC4-I bounded implementation
QW-LC4-F extension image and authorization freeze
QW-LC4-E sealed engineering execution
```

The extension compares `LOCAL_SWEEP` and `ANALYTIC_COMPLETION` only within the
registered scope. It does not open a scientific campaign or modify old evidence.

## Stage 32 — `QW-5`: single scientific-image freeze

After successful baseline and extension engineering reports, freeze one commit,
one image digest, `Torch2PC`, the code manifest, and schema versions. Code and
dependencies do not change across `C1/C2/C3/R`.

## Stage 33 — `C1`: collection and opportunity

Collect complete trajectories, `A0/A1/A2`, registered analytics, transition
cost, canonical suffix, and post-action labels. Test for sufficient intermediate
states and potential saving above control overhead.

## Stage 34 — `C2`: offline selection and policy freeze

Use only sealed `C1` artifacts. New model execution and labels are forbidden.
Select the simplest safe nearly non-dominated policy or record a negative
result.

## Stage 35 — `C3`: confirmatory shadow evaluation

On untouched model seeds, load the frozen policy, evaluate shadow proposals,
and always complete the canonical suffix for post-action audit.

## Stage 36 — `R`: replication without retuning

Repeat confirmatory evaluation with the preregistered configuration while
preserving image, policy, thresholds, and cost mapping.

## Stage 37 — synthesis and publication gate

Synthesize safety, coverage, complete cost, transferability limits, and negative
findings. Publication requires a separate receipt and does not open new
execution.

## Post-master's boundary — prospective PhD line

After the current critical path is complete, a separate `QWake-SPC` program may
move from QWake-PC
[spike-like control dynamics](docs/glossary_EN.md#term-spike-like-control-dynamics)
to native spikes, spike-native error transport, local learning, and
neuromorphic validation. This program is not Stage 21, does not open execution,
and does not change the master's-thesis completion criteria.


## Stage 25 — `QW-LC0`: semantics-and-scope freeze

Status: materialized on the branch. Contract `stage3b-qwake-lc0-semantics-scope-v1` freezes the
`R/M/Γ/C` separation, the `LOCAL_COMPUTE` family, the first-candidate scope, and
the claim boundary. Transition to `QW-LC1` is not permitted before merge.
Implementation, execution, and the scientific campaign remain closed.

```text
qwake_qw_lc0_semantics_scope_frozen=true
qwake_qw_lc1_transition_permitted=false
qwake_qw_lc1_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
next_slice=QW-LC0-repository-freeze
post_merge_next_slice=QW-LC1
```

## Stage 25 — `QW-LC0`: repository freeze

Status: materialized on the branch. The contract is merged into `main`
`8429f54257685a879b0a44499d5fa81eab7310ea` and reverified; a separate receipt binds the merge
commit, contract, and registry. Transition to `QW-LC1` is not permitted before
the receipt is merged.

```text
qwake_qw_lc0_repository_freeze_materialized=true
qwake_qw_lc0_repository_freeze_complete=false
qwake_qw_lc1_transition_permitted=false
qwake_qw_lc1_open=false
next_slice=QW-LC0-repository-freeze-merge
post_merge_next_slice=QW-LC1-transition
```

## Stage 26 — `QW-LC1`: transition to the required-result schema

Status: transition materialized on the branch. After merge and independent
verification, a separate slice may define the canonical `R(a,s)` schema,
mandatory observables, and `~R`. The `Γ` schema, cost mapping,
implementation, and execution are outside this stage.

```text
qwake_qw_lc1_transition_materialized=true
qwake_qw_lc1_transition_complete=false
qwake_qw_lc1_open=false
next_slice=QW-LC1-transition-merge
post_merge_next_slice=QW-LC1-required-response-schema
```
## Stage 26 — `QW-LC1`: required-response schema frozen

State: contract `stage3b-qwake-lc1-required-response-schema-v1` is materialized on the branch. `R(a,s)` consists
of named parameter gradients, endpoint beliefs, and scalar loss. Structural
fields are compared exactly; numerical entries are checked independently by the
zero-safe `~R` operator with CPU/float64 and ROCm/float32 profiles. State/RNG
and fallback remain in `QW-LC3`; `Γ`, `Φ`, `C`, and `~C` remain in `QW-LC2`.

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
next_slice=QW-LC1-repository-freeze
post_merge_next_slice=QW-LC1-repository-freeze
```
## Stage 27 — `QW-LC1`: repository freeze

Status: materialized on the branch. The schema was merged into `main`
`59e3143ba105a5b298e2cd551b221b8f6dae96f7` and reverified; a separate receipt binds the merge commit,
schema commit, contract, and registry. Until the receipt is merged, `QW-LC1`
is incomplete and transition to `QW-LC2` is not permitted.

```text
qwake_qw_lc1_repository_freeze_materialized=true
qwake_qw_lc1_repository_freeze_complete=false
qwake_qw_lc1_complete=false
qwake_qw_lc2_transition_permitted=false
resource_trajectory_schema_open=false
measurement_to_cost_mapping_open=false
cost_equivalence_operator_definition_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
next_slice=QW-LC1-repository-freeze-merge
post_merge_next_slice=QW-LC2-transition
```

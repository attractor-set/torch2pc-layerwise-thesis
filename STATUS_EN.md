# Research status

[Русская версия](STATUS.md)

As of 23 July 2026, the immutable Stage 1/2, Stage 3A, Stage 3B B0,
`SI-MA0`, and `SI-MA1` results are published. Confirmatory B1 and B2 are sealed
with positive decisions. The new `v2`
[matched-profiling](docs/glossary_EN.md#term-matched-profiling) package was
prospectively bound to those admissions and passed immutable-image,
ROCm/float32 preflight, authorization, and dry-run gates. All 288 cells in 96
matched blocks then completed, runtime validation passed, no failures or
retries occurred, and the compact evidence package is sealed and preserved.
The post-collection/pre-analysis descriptive protocol is frozen, and the
registered engine has passed full synthetic validation. Pre-execution
hardening verified provenance, consistency across the 288/1,440/96 compact
tables, and a real `Zstandard` frame. The machine-readable execution request, actual runtime preflight, and separate
authorization are frozen. The single read-only attempt completed on the verified
`main`; the exact 18-file output passed independent audit and is bound by an
external seal to the receipt and audit package. The output is published within
its bounded claim scope. `EX-IF0` now separately freezes `stage2_baseline` as the
canonical exact reference and freezes the minimum stably sufficient sweep rule;
execution, oracle-label generation, features, and control remain closed.

The full Stage 3B program remains incomplete.

## Machine-checkable current boundary

```text
matched_profiling_manifest_cells=288
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

These lines restate the existing contract; they do not create a new admission
decision.

## `QW-1`: pure QWake contract

The pure `QW-1` core is implemented without dependencies on Torch2PC, PyTorch,
GPU, filesystem, or subprocess execution. It freezes finite state,
observation, analytic, action, admission, cost, post-action oracle, and
provenance types; a deny-all permission model; role-bound allowlists; sealed
receipt requirements; and deterministic replay. The implementation does not
execute FixedPred and opens no scientific campaign.

```text
qwake_core_contract_implemented=true
qwake_core_contract_pure_python=true
qwake_core_contract_torch2pc_dependency=false
qwake_core_contract_gpu_dependency=false
qwake_permission_default=deny_all
qwake_capability_registry_closed=true
qwake_role_allowlists_fail_closed=true
qwake_receipt_chain_contract_implemented=true
qwake_deterministic_replay_contract_implemented=true
qwake_oracle_pre_action_access_permitted=false
qwake_scientific_execution_open=false
qwake_next_stage=QW-2
```

## `QW-2`: QWake-FP special-case contract

`QW-2` is complete as a pure, machine-readable freeze of the only mandatory
special case. The Python specification, `ADR-043`, canonical JSON, and
`SHA256SUMS` bind `FixedPred`, `eta=1`, `stage2_baseline`, `lenet_classic`, the
EX-IF0 endpoint defect, exact cumulative A0/A1/A2, the finite analytic registry,
B0-B7, P0-P2, cost mapping, and QW-1-inherited role/receipt rules. No execution
capability is opened.

```text
qwake_fp_special_case_contract_frozen=true
qwake_fp_special_case_contract_id=stage3b-qwake-fp-special-case-v1
qwake_fp_special_case_contract_sha256=968457365ddc1c94a814e0f7712d30d0154afd0c96d8464bff46a31e61ad3698
qwake_fp_method=fixedpred
qwake_fp_eta=1
qwake_fp_canonical_executor=stage2_baseline
qwake_fp_architecture=lenet_classic
qwake_fp_horizon_rule=registered_inference_steps
qwake_fp_observation_registry=A0,A1,A2
qwake_fp_analytic_registry=rosenbaum_wavefront_status_v1,residual_persistence_v1,cost_dominance_v1
qwake_fp_baseline_registry=B0,B1,B2,B3,B4,B5,B6,B7
qwake_fp_paired_validation=P0,P1,P2
qwake_fp_role_matrix_inherited_from_qw1=true
qwake_fp_scientific_execution_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
qwake_next_stage=QW-3
```

## Status summary

| Component | Verified state |
|---|---|
| Validation-only pilot | 96/96; the test dataset was not accessed |
| Stage 1 / Stage 2 | 80/80 and 80/80 |
| Stage 3A | confirmatory layer-wise diagnostics and publication complete |
| Stage 3B B0 | 96/96 ROCm/float32 cells; evidence and analysis published |
| `SI-MA0` | `REC/OBS/VER/CMP=true`, `COST=false`; global failure retained |
| `SI-MA1` | 10 `model_seed` values, 180 matched blocks; `CAL-COST-MA1=true`, final `pass` |
| B1/B2 theoretical prerequisite | the `PC-TREF`/`PC-CATM` package is published |
| B1/B2 preregistration | complete; tag `stage3b-b1-b2-prereg-v1` |
| B1 `isolated_layer_vjp` | confirmatory `EQ-B1=pass`; 120/120 pairs |
| B2 `composite_vjp` | `EQ-B2-CONFIRMATORY=pass`; 120/120 triples, 240/240 comparisons, 0 failed pairs; derived `EQ-B2` preserved |
| Matched-profiling request and manifest | previous version retained; production refresh required after confirmatory B2 |
| Matched-profiling runner | candidate-aware implementation complete |
| Matched-profiling execution | 288/288 cells, 96/96 blocks, 0 failures; sealed evidence preserved |
| Matched-profiling descriptive analysis | single attempt completed; 18 files audited, published through the bounded tagged action, and bound to the frozen publication receipt |
| `EX-IF0` | `stage2_baseline` frozen as canonical exact reference; suffix-stable sweep rule frozen; execution and labels closed |
| Test dataset | closed |
| Full Stage 3B | `full_stage3b_campaign_complete=false` |

## Published-result boundaries

### Stage 3A

Within FashionMNIST, `lenet_classic`, and `model_seed=0..9`:

- `FixedPred` nearly preserves gradient direction while attenuating its norm
  in early layers;
- `Strict` differs from BP in direction and scale in hidden layers;
- `FixedPred` representations are closer to BP than `Strict` representations;
- layers, batches, and samples are not treated as independent models.

These results are limited to the registered checkpoints, implementation, and
compute environment.

### Stage 3B B0

B0 fixes `stage2_baseline` for `FixedPred` and `Strict` in a synthetic
ROCm/float32 matrix. Within the registered scope:

- median Strict/FixedPred device-time ratio: `2.327×`;
- peak-allocated-memory ratio: `1.328×`;
- `state_inference` is the dominant time region;
- saved-tensor ratio within `state_inference`: `11.998×`.

This is descriptive engineering analysis, not a universal method ranking.

### `SI-MA0` and `SI-MA1`

`SI-MA0` retains a negative global outcome after `COST-MA0` failed.
`SI-MA1` separately tested observer calibration and completed with
`CAL-COST-MA1=true`, `SI-MA1=pass`. The `SI-MA1` result does not overwrite
`SI-MA0` and excludes the cost of a future `ECZ` evaluator, action selection,
[fallback](docs/glossary_EN.md#term-fallback) validation, and end-to-end B1/B2 benefit.

### B1/B2 admission

Confirmatory B1 passed CPU `float64` and ROCm `float32` controls over
120/120 pairs. B2 passed an engineering smoke and then the confirmatory campaign
over 120/120 triples and 240/240 direct comparisons.
`EQ-B2-CONFIRMATORY=pass` is sealed, and the derived `EQ-B2` is linked to it by
SHA-256. This admission chain supported the new `v2` matched-profiling run. The
execution is complete, but comparative conclusions have not yet been produced.

## Current transition

The sealed matched-profiling set is published at
`results/stage-3/profiling/matched/stage3b-matched-profiling-e1dcfb2-v1/`.
It contains 288 aggregate cells, 1,440 repetition rows, 96 matched-block
summaries, 288 append-only histories, 96 untimed correctness records, the
locality-event stream, the environment lock, and the runtime inventory. The
test split was not accessed.

After the single analysis attempt, independent audit, output sealing, and successful tagged publication action, the state is frozen as follows:

```text
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
full_stage3b_campaign_complete=false
```

The immutable tag and release package
`stage3b-matched-profiling-evidence-v1` are verified. A separate
post-collection/pre-analysis protocol freezes estimands, aggregation, the
Pareto rule, and `retain / conditional / reject_or_revise` decisions. The
bounded tagged publication action completed successfully, and the frozen
publication receipt binds the publication commit, successful workflow run,
release identifier, publication time, and asset digests. Publication does not authorize superiority claims or test-split access.
`EX-IF0 v1` separately selects `stage2_baseline` as canonical exact reference
and freezes the decision epoch, task-relative endpoint, oracle margin, and full
suffix stability for the minimum sufficient sweep. This design freeze does not
authorize `A11-OFF0`, oracle-label generation, feature collection, the
predictor, QWake-PC, or recursive-aggregate execution.

ADR-042 replaces the broad post-publication critical path with bounded
validation of one [QWake-FP](docs/glossary_EN.md#term-qwake-fp). General
QWake-PC remains a specification, while the mandatory experiment applies only
to corrected Rosenbaum FixedPred at `eta=1`. The next admissible stage is the
docs-only `QW-0`, followed by one permission-gated superset pipeline before a
single scientific-image freeze.

```text
qwake_general_specification_frozen=true
qwake_fp_only_mandatory_implementation=true
qwake_fp_validation_case=corrected_rosenbaum_fixedpred_eta1
execution_image_strategy=single_immutable_superset_image
same_image_digest_required_across_c1_c2_c3_r=true
stage_activation=fail_closed_permission_manifest
qwake_fp_execution_permitted=false
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
```

## Provenance

| Artifact | Identifier |
|---|---|
| B0 evidence | `stage3b-b0-evidence-v1` |
| B0 analysis | `stage3b-b0-analysis-evidence-v1` |
| `SI-MA1` preregistration | `stage3b-si-ma1-prereg-v1` |
| `SI-MA1` implementation | `stage3b-si-ma1-implementation-v1` |
| `SI-MA1` execution | `stage3b-si-ma1-confirmatory-execution-v1` |
| `SI-MA1` final | `stage3b-si-ma1-confirmatory-v1` |
| B1/B2 preregistration | `stage3b-b1-b2-prereg-v1` |
| Matched-profiling opening merge | `a249d35` |
| Candidate-aware runner implementation | `d611cb7` |
| Candidate-aware runner merge | `a44e7c8` |
| B2 confirmatory source | `63885e530fa38540ef684a6820a966eee96a58f9` |
| B2 confirmatory evidence | `stage3b-b2-confirmatory-63885e5-v1` |
| Matched-profiling execution source | `e1dcfb26823e1191b98d2aa2a598499b13197583` |
| Matched-profiling immutable image | `sha256:3c269b4278026b5b69968b3265b506ce626f2baf693859989de3371d639da4d0` |
| Matched-profiling evidence | `stage3b-matched-profiling-e1dcfb2-v1` |
| Published bounded release | `stage3b-matched-profiling-evidence-v1` |
| Publication action | `stage3b-matched-descriptive-analysis-publication-v1` |
| Publication receipt | `stage3b-matched-descriptive-analysis-publication-receipt-v1` |

Documentation changes do not regenerate published results.

## FixedPred sufficiency and D/U/S

ADR-039 freezes the next scoped continuation without execution permission:

```text
fixedpred_sufficiency_dus_design_frozen=true
fixedpred_sufficiency_method=fixedpred
fixedpred_sufficiency_exact_graph=stage2_baseline
rosenbaum_wavefront_role=analytic_positive_control
joint_vjp_role=exact_graph_organization_control
dus_controls_execution=false
oracle_label_generation_open=false
feature_collection_permitted=false
a11_off0_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

The next admissible slice is limited to refactoring and synthetic validation.
Frozen evidence, EX-IF0, historical identifiers, and published decisions remain
unchanged.

## Integrated frontier model

ADR-041 retains ADR-039 and ADR-040 as historical decisions and supplies the
current transition, admission, cost, and mandatory-scope semantics. O is
separate from deployable A0 -> A1 -> A2; analytics are independent measured
transitions, and DONE is an already admitted shadow outcome. The mandatory path
is temporal FixedPred, while recursive scales and active control remain
conditional. Scientific collection and closed data remain unavailable.

This corrective freeze removes documentation ambiguities but does not declare a positive scientific result or modify sealed evidence. Any subsequent experiment requires a separate admission decision.

```text
integrated_frontier_corrective_semantics_frozen=true
frontier_action_alphabet=ACCEPT_FRONTIER,ADVANCE_FRONTIER,COMPLETE_SUFFIX
frontier_advance_kinds=OBSERVATION,ANALYTIC,COMPUTE
deployable_observation_level_order=A0,A1,A2
oracle_level=O
oracle_availability=post_action_only
oracle_is_frontier_action=false
within_snapshot_observation_monotone=true
compute_transition_resets_current_observation=A0
analytic_registry_finite_and_frozen=true
measurement_to_decision_cost_mapping_required=true
done_semantics=admitted_shadow_outcome
mandatory_thesis_scope=temporal_fixedpred_prefix
recursive_multiscale_scope=conditional_extension
integrated_frontier_controls_execution=false
oracle_label_generation_open=false
feature_collection_permitted=false
a11_off0_execution_open=false
recursive_aggregate_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

## Bounded `QWake-FP` validation

[ADR-042](docs/decisions/ADR-042-stage3b-qwake-fp-bounded-validation-and-single-image-gating_EN.md)
freezes general QWake-PC as a specification and QWake-FP as the only mandatory
implementation. `C1_COLLECTION`, `C2_CALIBRATION`, `C3_CONFIRMATORY`, and
`R_REPLICATION` must use one image digest and differ only through hashed
request/policy manifests and permissions.

Permission is checked inside effectful functions. A disabled capability does
not execute. C2 is a strictly offline stage over sealed C1 artifacts: FixedPred,
new A0/A1/A2 collection, live analytics, new suffix/oracle computation, and
confirmatory access are forbidden there. Policy selection is permitted only in
C2. C3 uses untouched model seeds, and R uses the same policy without retuning.
Safety is evaluated before coverage, and coverage before cost.

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
permission_checks_at_effect_boundaries=true
disabled_capability_executes=false
policy_representation=frozen_data_manifest
policy_selection_with_confirmatory_access_forbidden=true
sealed_receipt_chain_required=true
untouched_confirmatory_seeds_required=true
replication_without_retuning_required=true
publication_baselines_required=true
nested_ablation_required=true
trajectory_benchmark_planned=true
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

## `QW-3` superset-pipeline implementation

`QW-3` implements the backend-neutral mandatory contour on top of `QW-1/QW-2`:
a closed embedded-component registry, effect-local planning, an immutable
trajectory schema, exact cumulative `A0/A1/A2`, a finite policy interpreter,
B0-B7 and nested ablations, non-duplicating cost mapping, opportunity and
recognizability, shadow/replication evaluation, pure sealing, and a
`rendered_not_published` publication bundle.

The module imports no Torch/Torch2PC, executes no FixedPred, reads no GPU, and
writes no artifacts. Live adapters are not yet bound; every campaign and the
scientific-image freeze remain closed. The next stage is `QW-4` pre-freeze
validation and canonical CPU/ROCm adapter/smoke binding.

```text
qwake_fp_superset_pipeline_implemented=true
qwake_fp_superset_pipeline_execution_open=false
qwake_fp_live_adapters_bound=false
qwake_fp_component_registry_closed=true
qwake_fp_offline_replay_implemented=true
qwake_fp_publication_export_mode=rendered_not_published
qwake_fp_next_stage=QW-4
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
```

## `QW-4A` pre-freeze validation harness and request freeze

`QW-4A` adds the pure validation harness and freezes the
`stage3b-qwake-fp-pre-freeze-validation-v1` request. It binds the QW-2 contract,
CPU/ROCm lanes, exact P0/P1/P2 equalities, observer measurements, negative
effect audits, A0/A1 nesting, post-action oracle isolation, cost mapping,
manifest integrity, and receipt-chain gates. The request is neither
authorization nor evidence.

The canonical FixedPred loader is registered as existing but unauthorized. New
observation/oracle/cost adapters remain unbound. Runtime smoke, the sealed
engineering report, and scientific-image freeze are not complete. The next step
is `QW-4B` runtime validation, not `QW-5`.

```text
qwake_fp_pre_freeze_validation_request_frozen=true
qwake_fp_pre_freeze_validation_request_id=stage3b-qwake-fp-pre-freeze-validation-v1
qwake_fp_pre_freeze_validation_harness_implemented=true
qwake_fp_pre_freeze_validation_complete=false
qwake_fp_runtime_authorization_issued=false
qwake_fp_pre_freeze_evidence_generated=false
qwake_fp_live_adapters_bound=false
qwake_fp_scientific_image_freeze_permitted=false
qwake_next_stage=QW-4-runtime-validation
qwake_fp_next_stage=QW-4-runtime-validation
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
```

## `QW-4B-I`: runtime-validation implementation

The deny-all runtime preflight, strict source/image/Torch2PC identity checks,
future single-run authorization validator, effect-local adapter symbols, a
concrete `stage2_baseline` Torch/Torch2PC backend, an all-snapshot observer, a
sequential matched runner with state/RNG restoration, a static-validation
receipt chain, and an authorization-only execution CLI are implemented. This
slice does not issue authorization, execute FixedPred autonomously, or create
evidence. The next step remains
`QW-4B-F` runtime freeze, not `QW-5`.

```text
qwake_fp_runtime_validation_implementation_complete=true
qwake_fp_runtime_preflight_implemented=true
qwake_fp_runtime_authorization_validator_implemented=true
qwake_fp_runtime_adapter_symbols_bound=true
qwake_fp_matched_runtime_runner_implemented=true
qwake_fp_runtime_report_sealer_implemented=true
qwake_fp_canonical_torch_backend_implemented=true
qwake_fp_all_snapshot_observer_implemented=true
qwake_fp_authorized_execution_cli_implemented=true
qwake_fp_static_validation_receipt_chain_implemented=true
qwake_fp_runtime_authorization_issued=false
qwake_fp_runtime_validation_performed=false
qwake_fp_pre_freeze_evidence_generated=false
qwake_fp_pre_freeze_validation_complete=false
qwake_fp_live_adapters_bound=false
qwake_fp_scientific_image_freeze_permitted=false
qwake_next_stage=QW-4-runtime-validation
qwake_fp_next_stage=QW-4-runtime-validation
qwake_fp_next_slice=QW-4-runtime-freeze
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
```

## `QW-4B-DOC-R1`: full active-plan refactor

The old `QW-4B-F-v1` candidate was retired before execution. Its bytes, logs,
and authorization remain in an external audit directory, but reuse is
forbidden. No engineering or scientific result was created.

The active plan now separates `R`, `M`, `Γ`, and `C`, introduces the
`LOCAL_COMPUTE` family, bounds the first analytic candidate, and establishes the
single sequence `QW-4B-F-v2 → QW-4B-E-v2 → QW-LC0…QW-LC4-E → QW-5 → C1 → C2
→ C3 → R`.

A new immutable image is required after this branch is merged. Only then may a
new preflight, receipt, and single-attempt authorization be issued.

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
qwake_next_slice=QW-4B-new-image
qwake_post_baseline_next_slice=QW-LC0
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

## `QW-4B-F-v2`: new image and single-attempt authorization frozen

After `QW-4B-DOC-R1` was merged, a new immutable image was built from merge commit `e413bb1e13cee42f702512e499f994e90df21e45`. Static, unit, and documentation validation passed again, followed by a new CPU/ROCm preflight and issuance of one engineering attempt.

The official verifier revalidated the authorization, and the source bytes were copied unchanged into `experiments/frozen/stage3b-qwake-fp-runtime-validation-freeze-v2`. The execution command was not called, the output root was not created, and engineering [evidence](docs/glossary_EN.md#term-evidence) is absent.

```text
qwake_documentation_refactor_complete=true
qwake_old_runtime_authorization_retired=true
qwake_old_runtime_authorization_reuse_permitted=false
qwake_new_image_required=false
qwake_new_image_built=true
qwake_new_image_source_commit=e413bb1e13cee42f702512e499f994e90df21e45
qwake_new_image_digest=sha256:bd91fab26df5f91a3aba90b8cad38badccab3a1a7bfb20efe4126a88a13236c4
qwake_new_runtime_preflight_captured=true
qwake_new_runtime_authorization_issued=true
qwake_runtime_authorization_verified=true
qwake_runtime_validation_permitted=true
qwake_runtime_execution_performed=false
qwake_runtime_validation_performed=false
qwake_engineering_evidence_present=false
qwake_fp_execution_permitted=false
qwake_frozen_preflight_sha256=sha256:79ead4a0e757272c788acd90700d61c0e5a0509fe64168f83f47dc0963ce4d00
qwake_frozen_authorization_sha256=sha256:d22063efa0c458c2498577139fa322b952081d8356cd1a6511f25188b12206b6
qwake_frozen_receipt_chain_sha256=sha256:9eda60c6806581fea28021546b881d939e062c017b702a175105c56a25dea05d
qwake_frozen_authorized_cell_count=6
qwake_frozen_execution_count=1
qwake_authorized_output_root_absent=true
qwake_scientific_image_freeze_permitted=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
qwake_next_slice=QW-4B-E-v2
qwake_post_baseline_next_slice=QW-LC0
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

## `QW-4B-E-v2`: baseline engineering report executed and independently recovered

The single authorized attempt ran from isolated source commit
`e413bb1e13cee42f702512e499f994e90df21e45`. The executor completed all six
`CPU/ROCm × P0/P1/P2` cells, and the immutable output is bound to report
`sha256:54dba01d47814dc00fa53bd69c00865bd1c47754c017c7482c895162d3a86b82`.

The post-execution wrapper failure and two later recovery-audit defects are
retained as provenance. Independent recovery-v3 verified authorization JSON and
model equality, both lanes, observation non-interference, oracle isolation, and
zero effects from disabled capabilities. Runtime execution was not repeated.

This slice materializes the exact output, complete audit package, and external
seal. The local-compute extension remains closed until the repository seal is
merged and `QW-LC0` semantics are opened separately. The report is engineering
only; scientific data, publication, and the test split remain closed.

```text
qwake_qw4b_e_v2_materialized=true
qwake_qw4b_e_v2_repository_evidence_sealed=false
qwake_qw4b_e_v2_runner_status=0
qwake_qw4b_e_v2_authorization_consumed=true
qwake_qw4b_e_v2_retry_permitted=false
qwake_qw4b_e_v2_runtime_rerun_performed=false
qwake_qw4b_e_v2_runtime_execution_performed=true
qwake_qw4b_e_v2_runtime_execution_completed=true
qwake_qw4b_e_v2_authorized_cell_count=6
qwake_qw4b_e_v2_cpu_lane_passed=true
qwake_qw4b_e_v2_rocm_lane_passed=true
qwake_qw4b_e_v2_engineering_evidence_present=true
qwake_qw4b_e_v2_image_freeze_eligible=true
qwake_qw4b_e_v2_report_sha256=sha256:54dba01d47814dc00fa53bd69c00865bd1c47754c017c7482c895162d3a86b82
qwake_qw4b_e_v2_scientific_evidence=false
qwake_qw4b_e_v2_scientific_execution_open=false
qwake_qw4b_e_v2_test_dataset_access=false
qwake_qw4b_e_v2_publication_permitted=false
qwake_qw_lc0_open=false
qwake_next_slice=QW-4B-E-v2-repository-seal
qwake_post_merge_next_slice=QW-LC0
```


## `QW-LC0`: post-merge transition opened

The `QW-4B-E-v2` repository seal was merged into `main` commit
`4f23b752a40ae05de9fc7ee49c9962c44083b71d`. All three evidence layers were reverified; their bytes
and digest identities remain unchanged.

Only the `QW-LC0` semantics-and-scope documentation freeze is opened.
`LOCAL_COMPUTE` implementation and execution, the scientific image, C1/C2/C3/R,
the test split, and publication remain closed.

```text
qwake_qw4b_e_v2_repository_evidence_sealed=true
qwake_qw4b_e_v2_repository_seal_commit=26bc0ef635e13dba719d3356fe17382f0037d1df
qwake_qw4b_e_v2_repository_merge_commit=4f23b752a40ae05de9fc7ee49c9962c44083b71d
qwake_qw4b_e_v2_post_merge_verification_passed=true
qwake_qw_lc0_transition_permitted=true
qwake_qw_lc0_open=true
qwake_qw_lc0_semantics_scope_frozen=false
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
qwake_next_slice=QW-LC0
qwake_post_lc0_next_slice=QW-LC1
```


## `QW-LC0`: semantics and scope frozen

Contract `stage3b-qwake-lc0-semantics-scope-v1` normatively separates `R/M/Γ/C`, freezes the two
`LOCAL_COMPUTE` members, and bounds the first candidate to `FixedPred`, `eta=1`,
`lenet_classic`, and `stage2_baseline`. It contains neither implementation nor
empirical validation of the candidate.

```text
qwake_qw_lc0_semantics_scope_frozen=true
qwake_qw_lc0_contract_id=stage3b-qwake-lc0-semantics-scope-v1
qwake_qw_lc0_contract_sha256=sha256:e68e953aa3d5c425678d54b8dd3b756e706e5cc1a1c4862d4c0ba0bda19bf3c3
qwake_qw_lc1_transition_permitted=false
qwake_qw_lc1_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC0-repository-freeze
qwake_post_merge_next_slice=QW-LC1
```

## `QW-LC0`: repository freeze materialized

Contract `stage3b-qwake-lc0-semantics-scope-v1` was merged into `main` by
`8429f54257685a879b0a44499d5fa81eab7310ea` and reverified with the 22-file tree unchanged. A separate
repository-state receipt is now materialized. Transition to `QW-LC1` remains
prohibited until that receipt is merged; implementation and execution stay
closed.

```text
qwake_qw_lc0_semantics_scope_frozen=true
qwake_qw_lc0_contract_id=stage3b-qwake-lc0-semantics-scope-v1
qwake_qw_lc0_contract_sha256=sha256:e68e953aa3d5c425678d54b8dd3b756e706e5cc1a1c4862d4c0ba0bda19bf3c3
qwake_qw_lc0_repository_main_commit=8429f54257685a879b0a44499d5fa81eab7310ea
qwake_qw_lc0_repository_freeze_materialized=true
qwake_qw_lc0_repository_freeze_complete=false
qwake_qw_lc1_transition_permitted=false
qwake_qw_lc1_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC0-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC1-transition
```

## `QW-LC1`: transition materialized

The `QW-LC0` repository freeze is complete after merge and independent
verification of `main` `0fbd54be337665e06ad63b6d9c7f8ca978ab75ee`. A separate transition
receipt is materialized. It limits the future `QW-LC1` slice to the required
result schema `R(a,s)`, mandatory observables, and `~R`, without defining their
content. Until the transition is merged, `QW-LC1`, trajectory `Γ`, cost,
implementation, and execution remain closed.

```text
qwake_qw_lc0_repository_freeze_complete=true
qwake_qw_lc1_transition_permitted=true
qwake_qw_lc1_transition_materialized=true
qwake_qw_lc1_transition_complete=false
qwake_qw_lc1_transition_id=stage3b-qwake-lc1-transition-v1
qwake_qw_lc1_transition_sha256=sha256:9cafcad4d6ee3245c48ca2ff531dc5985ea4e670cb465fdcfaf2b99d376d5db4
qwake_qw_lc1_open=false
qwake_qw_lc1_required_response_schema_open=false
mandatory_observables_definition_open=false
response_equivalence_operator_definition_open=false
resource_trajectory_schema_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC1-transition-merge
qwake_post_merge_next_slice=QW-LC1-required-response-schema
```
## `QW-LC1`: required-response schema frozen

The `QW-LC1` transition was merged into `main` `c3533fcb63ffc869faddbaa99645c9099d16d1cc` and
independently reverified. Contract `stage3b-qwake-lc1-required-response-schema-v1` freezes canonical `R(a,s)`,
mandatory response observables, and the zero-safe `~R` operator. Exact digest
equality is sufficient but not required; the tolerance predicate is not assumed
transitive. The schema contains no implementation and establishes no candidate.

```text
qwake_qw_lc1_transition_complete=true
qwake_qw_lc1_required_response_schema_permitted=true
qwake_qw_lc1_open=true
qwake_qw_lc1_required_response_schema_frozen=true
qwake_qw_lc1_contract_id=stage3b-qwake-lc1-required-response-schema-v1
qwake_qw_lc1_contract_sha256=sha256:c7923249c538b29a34f8ffcfcac987b9925a911eb107a085a166ab1d7ca22992
qwake_qw_lc1_contract_registry_sha256=sha256:4a5dca3848bd8ffb0f70013fb5c42a6f6427dd0e1752eb950f5332207b8e269f
mandatory_observables_definition_frozen=true
response_equivalence_operator_definition_frozen=true
qwake_qw_lc1_complete=false
qwake_qw_lc2_transition_permitted=false
resource_trajectory_schema_open=false
measurement_to_cost_mapping_open=false
cost_equivalence_operator_definition_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC1-repository-freeze
qwake_post_merge_next_slice=QW-LC1-repository-freeze
```
## `QW-LC1`: repository freeze materialized

The required-response schema was merged into `main` `59e3143ba105a5b298e2cd551b221b8f6dae96f7` and
independently reverified. Schema commit `de2b5a37583b22946073390caa244bee35dd793b` is preserved
as the second parent, the exact 22-file scope and schema tree are unchanged,
and the contract and registry have the expected checksums.

Two-file receipt `stage3b-qwake-lc1-repository-freeze-v1` binds that `main` state to
contract `stage3b-qwake-lc1-required-response-schema-v1`. Until the receipt is merged and separately
reverified, `QW-LC1` remains incomplete, transition to `QW-LC2` is prohibited,
and resource trajectory, cost, implementation, and execution remain closed.

```text
qwake_qw_lc1_required_response_schema_merged=true
qwake_qw_lc1_schema_main_commit=59e3143ba105a5b298e2cd551b221b8f6dae96f7
qwake_qw_lc1_schema_commit=de2b5a37583b22946073390caa244bee35dd793b
qwake_qw_lc1_repository_freeze_materialized=true
qwake_qw_lc1_repository_freeze_complete=false
qwake_qw_lc1_complete=false
qwake_qw_lc2_transition_permitted=false
resource_trajectory_schema_open=false
measurement_to_cost_mapping_open=false
cost_equivalence_operator_definition_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC1-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC2-transition
```

## `QW-LC2`: transition materialized

The `QW-LC1` repository freeze is complete after merge and independent
verification of `main` `9d073bc3c90eeda53ca03d0f7762b65da8749269`. A separate transition receipt is
materialized. It limits future `QW-LC2` to the `Γ(a,s)` measurement schema,
`Φ: Γ -> C`, and `~C`, without defining fields, units, tolerances, or values.
Until the transition is merged, `QW-LC2`, implementation, and execution remain
closed.

```text
qwake_qw_lc1_repository_freeze_complete=true
qwake_qw_lc1_complete=true
qwake_qw_lc2_transition_permitted=true
qwake_qw_lc2_transition_materialized=true
qwake_qw_lc2_transition_complete=false
qwake_qw_lc2_transition_id=stage3b-qwake-lc2-transition-v1
qwake_qw_lc2_transition_sha256=sha256:9a7e21fa573aa497e5c85ab92aade9e84e15dc0bd05e18e948ad8fac0194df23
qwake_qw_lc2_open=false
resource_trajectory_schema_open=false
measurement_to_cost_mapping_open=false
cost_equivalence_operator_definition_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC2-transition-merge
qwake_post_merge_next_slice=QW-LC2-resource-cost-contract
```

## `QW-LC2`: resource and cost contract materialized

After merge and independent verification of the transition on `main`
`858403cbb2423ad3427ab7a042266880ca34c0b7`, contract `stage3b-qwake-lc2-resource-cost-contract-v1` was materialized. It freezes
canonical raw `Γ(a,s;r,p)`, a no-double-counting `Φ`, an 11-field `C`, two cost
profiles, fieldwise `~C`, a Pareto rule, and deterministic ambiguity
resolution. State/RNG/fallback validation, repeat aggregation, implementation,
and execution remain later slices.

```text
qwake_qw_lc2_transition_complete=true
qwake_qw_lc2_open=true
qwake_qw_lc2_resource_cost_contract_frozen=true
qwake_qw_lc2_contract_id=stage3b-qwake-lc2-resource-cost-contract-v1
qwake_qw_lc2_contract_sha256=sha256:313dc969ab59db20ee27976d3158fca23ce511801e0dc7700dde0d2d002ab69d
qwake_qw_lc2_contract_registry_sha256=sha256:61763ad19c968dbad3eef16e5bee3a11d9dbfad74a7bf45dfc2e64cc022cf311
resource_trajectory_schema_open=false
resource_trajectory_schema_frozen=true
measurement_to_cost_mapping_open=false
measurement_to_cost_mapping_frozen=true
cost_equivalence_operator_definition_open=false
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
runtime_rerun_performed=false
qwake_next_slice=QW-LC2-repository-freeze
```

## `QW-LC2`: repository freeze materialized

Contract `stage3b-qwake-lc2-resource-cost-contract-v1` was merged into `main` `8f24229bcf19736086fe6f0340bda26dd533936a` and independently
reverified. Receipt `stage3b-qwake-lc2-repository-freeze-v1` binds that state
to contract commit `3f1682765089b0819dcaaf9bb449c4c1bd155142` and its exact checksums.

Until receipt merge, `QW-LC2` is incomplete, while `QW-LC3`, implementation,
and execution remain closed.

```text
qwake_qw_lc2_resource_cost_contract_merged=true
qwake_qw_lc2_resource_cost_contract_complete=true
qwake_qw_lc2_contract_id=stage3b-qwake-lc2-resource-cost-contract-v1
qwake_qw_lc2_contract_sha256=sha256:313dc969ab59db20ee27976d3158fca23ce511801e0dc7700dde0d2d002ab69d
qwake_qw_lc2_repository_main_commit=8f24229bcf19736086fe6f0340bda26dd533936a
qwake_qw_lc2_resource_cost_commit=3f1682765089b0819dcaaf9bb449c4c1bd155142
qwake_qw_lc2_repository_freeze_materialized=true
qwake_qw_lc2_repository_freeze_complete=false
qwake_qw_lc2_complete=false
qwake_qw_lc3_transition_permitted=false
resource_trajectory_schema_frozen=true
measurement_to_cost_mapping_frozen=true
cost_equivalence_operator_definition_frozen=true
pareto_and_tie_break_rule_frozen=true
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
qwake_next_slice=QW-LC2-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC3-transition
```

## `QW-LC3`: transition materialized

The `QW-LC2` repository freeze completed after merge and independent
verification of `main` `4f7c533047214398e7ec4dde9d58b5fc06964b90`. Freeze commit
`3f4310a05de5b7cd3db0cdb5c8f7cf4bbcb09150` remains in the graph, the tree is
preserved, and the repository receipt and resource contract have their expected
checksums.

A separate transition receipt, `stage3b-qwake-lc3-transition-v1`, was
materialized. It limits future `QW-LC3` work to matched shadow validation,
opaque shared-state identity, RNG restoration, a complete exact-reserve suffix,
and matched repeat aggregation. Until transition merge, `QW-LC3`, its
definitions, implementation, and execution remain closed.

```text
qwake_qw_lc2_repository_freeze_complete=true
qwake_qw_lc2_complete=true
qwake_qw_lc3_transition_permitted=true
qwake_qw_lc3_transition_materialized=true
qwake_qw_lc3_transition_complete=false
qwake_qw_lc3_transition_id=stage3b-qwake-lc3-transition-v1
qwake_qw_lc3_transition_sha256=sha256:c541703f8bc1d449aed88f175b83b9fc03e2574acb5c2be715b157be68733602
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
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
qwake_next_slice=QW-LC3-transition-merge
qwake_post_merge_next_slice=QW-LC3-matched-shadow-validation-contract
```

## `QW-LC3`: matched shadow-validation contract materialized

After the PR #120 transition merge into `main`
`a7e0c4ec1978042d68abc7437e3005e4295e75ff` was independently verified,
contract `stage3b-qwake-lc3-matched-shadow-validation-contract-v1` was
materialized. It freezes a canonical opaque shared-state reference, complete
RNG inventory and restoration, twelve balanced matched repeats, two forced
complete exact-reserve suffix probes, componentwise cost aggregation, and a
separate order-effect gate.

Every arm and reserve probe starts from a fresh disposable fork of one immutable
snapshot. `~R` must pass for all twelve pairs; repeat exclusion, majority voting,
and cost scalarization are forbidden. The contract contains no implementation
and reports no empirical result.

```text
qwake_qw_lc3_transition_complete=true
qwake_qw_lc3_open=true
qwake_qw_lc3_matched_shadow_validation_contract_frozen=true
qwake_qw_lc3_contract_id=stage3b-qwake-lc3-matched-shadow-validation-contract-v1
qwake_qw_lc3_contract_sha256=sha256:e1512f29b3e3e3882001172df360e895e6e628b8ea8e4103b9574990775dd5d8
qwake_qw_lc3_contract_registry_sha256=sha256:2b001f3002add8d55ce75b02b1caba6bd3c655d177aeb02fe09026e2054dcef1
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

## `QW-LC3`: repository freeze materialized

Contract `stage3b-qwake-lc3-matched-shadow-validation-contract-v1` was merged through PR #121 into
`main` `71e73f56408c720334b8fa03e7133762c8bbcc43` and independently verified. Receipt
`stage3b-qwake-lc3-repository-freeze-v1` binds that state to contract commit
`fb3f1cd4a4d3b4261db1179badcc1ccacddfe936` and its checksums.

Until the receipt is merged, `QW-LC3` remains incomplete, while `QW-LC4-I`,
implementation, and execution remain closed.
The freeze confirms only the integrity of the already accepted validation description. It establishes neither future algorithm correctness, response equivalence, cost reduction, nor scientific-run readiness.
The recorded state remains preparatory: it preserves decision provenance, prevents silent scope expansion, and requires a separate authorization for every later step. Any computation before that authorization is prohibited and cannot be treated as a research result.

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

## `QW-LC4-I`: bounded implementation materialized

The `QW-LC3` repository freeze was merged through PR #122 into `main`
`7c6cbb6ba4941cf78b2bfec3e6e8955c2830a58b` and independently verified.
`QW-LC3` is complete. Implementation package
`stage3b-qwake-lc4-i-bounded-implementation-v1` now binds the bounded
`FixedPred`, `eta=1` analytic candidate, the complete exact suffix, canonical
state and RNG controls, the `QW-LC1` response predicate, the `QW-LC2` cost
mapper, and the balanced twelve-repeat aggregation.

The only executable permit in this slice is synthetic-unit-test-only. The
module has no CLI, dataset loader, output writer, runtime authorization reader,
or scientific executor. Its synthetic tests are not engineering or scientific
evidence and do not establish runtime response equivalence or cost superiority.

```text
qwake_qw_lc3_repository_freeze_merged=true
qwake_qw_lc3_repository_freeze_complete=true
qwake_qw_lc3_complete=true
qwake_qw_lc4_i_authoring_open=true
qwake_qw_lc4_i_implementation_materialized=true
qwake_qw_lc4_i_implementation_id=stage3b-qwake-lc4-i-bounded-implementation-v1
qwake_qw_lc4_i_implementation_sha256=sha256:4dc7b123e2af3a09d675550e52aff361146a744bcf5b4717b426137d44b88dfa
qwake_qw_lc4_i_implementation_registry_sha256=sha256:f1ca469d3aeb3fe5c4a90f6bdb068a61444bf9b8eb0efe25b29121821c990894
qwake_qw_lc4_i_complete=false
qwake_qw_lc4_f_branch_permitted=false
qwake_bounded_analytic_candidate_materialized=true
qwake_complete_exact_suffix_materialized=true
qwake_opaque_state_ref_implementation_materialized=true
qwake_rng_restoration_implementation_materialized=true
qwake_required_response_mapper_materialized=true
qwake_resource_cost_mapper_materialized=true
qwake_paired_aggregation_materialized=true
qwake_synthetic_unit_test_only=true
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
qwake_next_slice=QW-LC4-I-merge
qwake_post_merge_next_slice=QW-LC4-F
```

## `QW-LC4-F`: runtime-freeze authoring materialized

The bounded `QW-LC4-I` implementation merged through PR #123 into `main`
`c9f3dadcd5330887584b8bf71d906c667dacf076` and was independently verified.
Authoring package `stage3b-qwake-lc4-f-runtime-freeze-authoring-v1`
materializes the runtime frontier adapter, deny-all preflight, exact
single-attempt engineering authorization schema, and an executor-free sealing
boundary.

A separate request freezes two lanes, candidate indices `0..6`, twelve repeats
per combination, and two exact reserve probes. The matrix contains 14 runtime
cells, 168 matched-pair cells, and 28 reserve probes. None is executed in this
slice.

The actual image digest is not frozen yet: the authoring slice must first be
committed, then the image must be built from that exact commit. The runtime
freeze itself and `QW-LC4-E` therefore remain closed.

```text
qwake_qw_lc4_i_merged=true
qwake_qw_lc4_i_complete=true
qwake_qw_lc4_i_merge_commit=c9f3dadcd5330887584b8bf71d906c667dacf076
qwake_qw_lc4_f_authoring_open=true
qwake_qw_lc4_f_authoring_materialized=true
qwake_qw_lc4_f_authoring_id=stage3b-qwake-lc4-f-runtime-freeze-authoring-v1
qwake_qw_lc4_f_authoring_sha256=sha256:c0a11996708b091e737a0bfa60e2a000f65b9e9f0971e8c3041838f25922860a
qwake_qw_lc4_f_authoring_registry_sha256=sha256:a59af6fe70612277ceaecba9a86a2dc49dcb2612154993d9c7cc10d8c3bcb7f4
qwake_qw_lc4_f_request_frozen=true
qwake_qw_lc4_f_request_id=stage3b-qwake-lc4-f-runtime-freeze-request-v1
qwake_qw_lc4_f_request_sha256=sha256:bc4e36f9265837dc0a36f0eca039b057a5113c4ef872f72e1698db5bc4930506
qwake_qw_lc4_f_request_registry_sha256=sha256:0a58be97a03c7283cf1b46e5815e7ca58271b4b61a29cd53566fa6d7600212ea
qwake_qw_lc4_f_runtime_module_sha256=sha256:003759e0eac5062e34b0ead1f24c1e1babb09f096023539ac3303a2af9957a7c
qwake_qw_lc4_f_adapter_registry_sha256=sha256:40397474de6c97663ac44c718d4c52846a4ba077bc5343a0d10114afd576bbde
qwake_qw_lc4_f_runtime_cell_count=14
qwake_qw_lc4_f_matched_pair_count=168
qwake_qw_lc4_f_reserve_probe_count=28
qwake_qw_lc4_f_materialized=false
qwake_qw_lc4_f_complete=false
qwake_qw_lc4_e_branch_permitted=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
qwake_next_slice=QW-LC4-F-authoring-commit
qwake_post_commit_next_slice=QW-LC4-F-runtime-materialization
```
## `QW-LC4-F`: runtime freeze materialized

See [ADR-063](docs/decisions/ADR-063-stage3b-qwake-lc4-f-runtime-freeze_EN.md).

The exact authoring commit is bound to the image, CPU/ROCm checks, the
22-check static chain, one-attempt authorization, and the ten-file
`stage3b-qwake-lc4-f-runtime-freeze-v1` package.

Authorization is not execution. Until merge and independent post-merge
verification, `QW-LC4-F` remains incomplete, `QW-LC4-E` is prohibited, and
scientific and publication capabilities remain closed.

```text
qwake_adr=ADR-063-stage3b-qwake-lc4-f-runtime-freeze
qwake_source_commit=51fc7537fdcb395145fc4c5a38b8918b018fe892
qwake_image_digest=sha256:a31cf96e20ab45ce29fe18b68eb805bd048a02f1f8107cf680d1c174ea363929
qwake_preflight_sha256=sha256:3a8d7817338f3b93396270ea8e1b1b2fbda768dbd5461a18f97520948a53a9e6
qwake_authorization_sha256=sha256:d11b662a5c5eeada5333e69c6fddf2e50726c01b4d8c78a556a68167dbdd301e
qwake_next_slice=QW-LC4-F-merge
qwake_post_merge_next_slice=QW-LC4-E
QW_LC4_F_MATERIALIZED=true
QW_LC4_F_COMPLETE=false
QW_LC4_E_BRANCH_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
```
## `QW-LC4-E`: admission authoring materialized

See [ADR-064](docs/decisions/ADR-064-stage3b-qwake-lc4-e-execution-admission-authoring_EN.md).

A pure schema and validator for a future one-attempt admission were added.
They verify the exact `QW-LC4-F` package, operator acknowledgement, and absence
of the result root and lease. No model executor or admission record exists.

```text
qwake_adr=ADR-064-stage3b-qwake-lc4-e-execution-admission-authoring
QW_LC4_F_COMPLETE=true
QW_LC4_E_BRANCH_OPEN=true
EXECUTION_ADMISSION_IMPLEMENTED=true
EXECUTION_ADMISSION_ISSUED=false
QW_LC4_E_EXECUTION_PERMITTED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```
## `QW-LC4-E`: concrete admission frozen

See [ADR-065](docs/decisions/ADR-065-stage3b-qwake-lc4-e-execution-admission-freeze_EN.md).

The five-file package is bound to `main` `bce821dff0729629db0ccb306d8f3fd1dd9a2e13`. The admission permits one
engineering attempt, but no lease, executor, or result root exists. The
branch-level execution gate remains closed.

```text
qwake_adr=ADR-065-stage3b-qwake-lc4-e-execution-admission-freeze
qwake_admission_sha256=sha256:d1ee6d022588f0a2cf0ac23f3bf8de9b27f9aad4fc1153435bd70e1ab83e296c
qwake_admission_file_sha256=sha256:d819f8a7e03314242c0072e2d020a59fbe6b7f6984fda99ff0dcd306cc97ca70
qwake_admission_receipt_sha256=sha256:d4b9d33117cbf522b1c62173c7a81f9638cde703eb6b3bbb392ff46e45a17c25
qwake_admission_package_registry_sha256=sha256:411f3e8d62b367755a6f02070ad84bc6f37cfefad602d885674a844b57aa74cd
QW_LC4_E_AUTHORING_MERGED=true
ADMISSION_FREEZE_BRANCH_OPEN=true
ADMISSION_FREEZE_MATERIALIZED=true
EXECUTION_ADMISSION_ISSUED=true
ADMISSION_RECORD_RUNTIME_EXECUTION_PERMITTED=true
QW_LC4_E_EXECUTION_PERMITTED=false
AUTHORIZATION_CONSUMED=false
EXECUTION_LEASE_PRESENT=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```
## `QW-LC4-E`: lease and wrapper contract authoring

See [ADR-066](docs/decisions/ADR-066-stage3b-qwake-lc4-e-execution-lease-wrapper-authoring_EN.md).

The slice reverifies the merged admission and constructs a prospective
one-attempt lease and future wrapper contract only in memory. No lease writer,
runtime executor, or result writer exists.

```text
qwake_adr=ADR-066-stage3b-qwake-lc4-e-execution-lease-wrapper-authoring
qwake_lease_test_vector_sha256=sha256:66961a641d7f9cc9b7b2f958c432a492c1ada171056b827136171dd0df2b355a
qwake_wrapper_contract_test_vector_sha256=sha256:0ff0cf0b0f23bf21d65567079212e5bad04e16e257815143d3f581664fa4dbf0
ADMISSION_FREEZE_MERGED=true
EXECUTION_LEASE_WRAPPER_AUTHORING_BRANCH_OPEN=true
EXECUTION_LEASE_SCHEMA_IMPLEMENTED=true
EXECUTION_WRAPPER_CONTRACT_IMPLEMENTED=true
EXECUTION_LEASE_MATERIALIZED=false
EXECUTION_LEASE_WRITER_PRESENT=false
RUNTIME_EXECUTOR_PRESENT=false
RESULT_WRITER_PRESENT=false
QW_LC4_E_EXECUTION_PERMITTED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

### Execution-control state clarification

This stage specifies only the verifiable rules for a future run. It does not
create an ownership file, consume the authorization, or invoke model
computation. A separate implementation must preserve a single exclusive
attempt, atomic state transitions, immutable inputs, and fail-closed behavior
for every error. Execution, result production, and evidence publication remain
forbidden until that implementation passes independent verification.

## `QW-LC4-E`: atomic lease/wrapper implementation

See [ADR-067](docs/decisions/ADR-067-stage3b-qwake-lc4-e-execution-lease-wrapper-implementation_EN.md).

A separate effect implementation follows the merged and independently verified
authoring slice. It provides a temporary-file plus hard-link exclusive lease
claim, a post-claim output race check, an injected backend confined to a hidden
staging directory, and Linux `renameat2(RENAME_NOREPLACE)` promotion of a
complete result tree.

The lease persists after every failure, retry after claim is prohibited,
partial staging output is removed, and an existing result tree is never
replaced. The verifier exercises these mechanics only under `/tmp`; it leaves
the repository lease and runtime output absent.

Implementation availability is not execution authorization. No real invocation
command or immutable execution freeze is present, so authorization consumption,
runtime execution, evidence, science, test-data access, and publication remain
closed.

```text
qwake_adr=ADR-067-stage3b-qwake-lc4-e-execution-lease-wrapper-implementation
qwake_implementation_json_sha256=sha256:f7cb2c72f5e9516d808f8f76802e2e560579f407aa1e155675bae2570a09b08e
qwake_implementation_registry_sha256=sha256:348b574bf7093edd4db263779014c256209a38b1c9e4c78f9598d0f82bf8b59a
LEASE_WRAPPER_AUTHORING_MERGED=true
LEASE_WRAPPER_IMPLEMENTATION_BRANCH_OPEN=true
LEASE_WRAPPER_IMPLEMENTATION_MATERIALIZED=true
EXECUTION_LEASE_SCHEMA_IMPLEMENTED=true
EXECUTION_WRAPPER_CONTRACT_IMPLEMENTED=true
EXECUTION_LEASE_WRITER_PRESENT=true
RUNTIME_EXECUTOR_PRESENT=true
RESULT_WRITER_PRESENT=true
EXECUTION_LEASE_MATERIALIZED=false
QW_LC4_E_EXECUTION_PERMITTED=false
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

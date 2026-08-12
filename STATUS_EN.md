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
## `QW-LC4-E`: execution-freeze authoring

See [ADR-068](docs/decisions/ADR-068-stage3b-qwake-lc4-e-execution-freeze-authoring_EN.md).

PR #128 merged into `main` as
`24966cd2a0380e46ab1924ff4ab8987f17e1fe9e`; its exact implementation tree and
CI passed independent verification. A new pure contract binds that state to the
frozen admission and builds a deterministic execution-freeze request.

The check exposes a required incomplete boundary: the generic wrapper exists,
but the concrete backend that obtains real FixedPred frontier states and the
one-shot invocation entrypoint do not. The immutable execution image,
execution freeze, and run permission therefore remain closed.

```text
qwake_adr=ADR-068-stage3b-qwake-lc4-e-execution-freeze-authoring
qwake_execution_freeze_request_sha256=sha256:9b28943043082efe96fb313f94875ef18c7f8e7361d8c0eb1b8c140e82a1e312
qwake_authoring_json_sha256=sha256:9dfe3177442abdbe255047732a33d02d0987e4d634f0b1c629e1671fc68677dd
qwake_authoring_registry_sha256=sha256:9b65ba87c817fa67670ab4e225f15e9b1f2544459439cda2e5e0b621b324ca53
LEASE_WRAPPER_IMPLEMENTATION_MERGED=true
EXECUTION_FREEZE_BRANCH_OPEN=true
EXECUTION_FREEZE_CONTRACT_MATERIALIZED=true
CONCRETE_RUNTIME_BACKEND_PRESENT=false
ONE_SHOT_ENTRYPOINT_PRESENT=false
IMMUTABLE_EXECUTION_IMAGE_PRESENT=false
EXECUTION_FREEZE_MATERIALIZED=false
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

## `QW-LC4-E`: bounded runtime backend

See [ADR-069](docs/decisions/ADR-069-stage3b-qwake-lc4-e-runtime-backend-implementation_EN.md).

A separate slice materializes the concrete backend for the frozen synthetic
`2 × 7 × 12` matrix, 28 exact-reserve probes, and a one-shot entrypoint. The
backend does not read a dataset and has no import-time execution effect. The
future command must first verify the exact `execution-freeze-v1` package,
Torch2PC commit, code SHA-256 values, and immutable image digest; while that
package is absent it stops before claiming a lease.

Real `lenet_classic` frontiers use a pure canonicalization of only already
completed upper errors to `fixed - beliefs` within a strict tolerance. Raw and
canonical frontiers retain separate SHA-256 values. A tolerance violation
fails closed. Negative empirical `~R`, RNG, reserve-path, or order-effect
outcomes are preserved as engineering evidence rather than discarded after a
single-attempt admission.

```text
qwake_adr=ADR-069-stage3b-qwake-lc4-e-runtime-backend-implementation
RUNTIME_BACKEND_BRANCH_OPEN=true
CONCRETE_RUNTIME_BACKEND_PRESENT=true
ONE_SHOT_ENTRYPOINT_PRESENT=true
RUNTIME_EXECUTION_FREEZE_GUARD_PRESENT=true
FRONTIER_ROUNDOFF_CANONICALIZATION_PRESENT=true
NEGATIVE_VALIDATION_EVIDENCE_PRESERVED=true
IMMUTABLE_EXECUTION_IMAGE_PRESENT=false
EXECUTION_FREEZE_MATERIALIZED=false
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
```

### `QW-LC4-E` execution-freeze materialization

See [ADR-070](docs/decisions/ADR-070-stage3b-qwake-lc4-e-execution-freeze-materialization_EN.md).

- PR #130 merged into `main` `67a084c0b970ad79ad0692442f660085a73b080a` and passed independent verification;
- immutable image `torch2pc-layerwise-thesis:0.1.0-qw-lc4-e-freeze-67a084c0b970` was built from that commit with identity `sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d`;
- the nine-file `execution-freeze-v1` package binds the image, backend, entrypoint, admission, and authorization;
- raw `image-build.log` bytes are preserved exactly and the single path is classified in `.gitattributes` as sealed binary evidence;
- the internal record enables the future one-shot entrypoint, but the branch-level execution gate remains closed;
- no lease, output root, engineering evidence, scientific execution, test-dataset access, or publication exists.

## `QW-LC4-E`: one-shot engineering invocation authorization

See [ADR-071](docs/decisions/ADR-071-stage3b-qwake-lc4-e-one-shot-invocation-authorization_EN.md).

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

## `QW-LC4-E`: one-shot host invocation-wrapper authoring

See [ADR-072](docs/decisions/ADR-072-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-authoring_EN.md).

After post-merge verification of PR #132, a separate pure module freezes the
future host invocation boundary. The contract requires the exact image repo
digest, source-label verification, disabled networking, a read-only root
filesystem, and a dedicated `/tmp` tmpfs. It permits exactly three bind mounts,
requires `/dev/kfd` and `/dev/dri`, fixes user/group and resource-input wiring,
and forbids binding the project source tree or a dataset.

This slice contains no `subprocess`, container-runtime invocation, or
materialized command. It only reverifies authorization and constructs the
canonical prospective contract in memory and under a temporary verifier
directory.

```text
qwake_adr=ADR-072-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-authoring
qwake_invocation_wrapper_contract_sha256=sha256:4c4cb163e8c2a33b0563cc3b9cb873a87acf8ea75bb3e807d157d51c5a4dd29b
INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
INVOCATION_WRAPPER_AUTHORING_BRANCH_OPEN=true
INVOCATION_WRAPPER_CONTRACT_PRESENT=true
CONTAINER_COMMAND_TEMPLATE_PRESENT=true
GPU_DEVICE_BINDING_COUNT=2
TMPFS_REQUIRED=true
TMPFS_TARGET=/tmp
HOST_RUNTIME_INVOKER_PRESENT=false
IMAGE_INSPECTION_IMPLEMENTED=false
INVOCATION_COMMAND_MATERIALIZED=false
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

## `QW-LC4-E`: one-shot host invocation-wrapper implementation

See [ADR-073](docs/decisions/ADR-073-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-implementation_EN.md).

After post-merge verification of PR #133, a separate module implements exact
inspection of the local immutable image. Its only external operation is
`docker image inspect` of the exact image repo digest; the tag, image ID, every
layer, source label, `SOURCE_GIT_COMMIT`, entrypoint, and working directory are
compared with `execution-freeze-v1`.

The future invocation is materialized only as a canonical in-memory argv tuple.
It forbids image pulling, networking, privileged mode, excess capabilities,
project-source mounts, and [dataset](docs/glossary_EN.md#term-dataset) access.
The command is neither persisted nor executed.

```text
qwake_adr=ADR-073-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-implementation
IMAGE_INSPECTION_IMPLEMENTED=true
INVOCATION_COMMAND_MATERIALIZED=true
INVOCATION_COMMAND_PERSISTED=false
HOST_RUNTIME_INVOKER_PRESENT=false
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

## `QW-LC4-E`: one-shot host-runtime-invoker authoring

See [ADR-074](docs/decisions/ADR-074-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-authoring_EN.md).

After post-merge verification of PR #134, a separate pure contract binds the
canonical argv implementation to one future child-container spawn. The host
reinspects the image and command but cannot write the execution lease: atomic
claim remains owned by the container entrypoint in the same process that then
invokes the backend.

The contract freezes no-shell argv execution, one child spawn, no automatic
retry after spawn, timeout, signal forwarding, bounded output capture, and
lease persistence after failure. The invoker itself remains absent.

```text
qwake_adr=ADR-074-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-authoring
HOST_RUNTIME_INVOKER_CONTRACT_PRESENT=true
HOST_RUNTIME_INVOKER_PRESENT=false
HOST_RUNTIME_INVOKER_EXECUTABLE=false
HOST_DOCKER_RUN_IMPLEMENTED=false
EXACT_ARGV_ONLY=true
SHELL_INTERPRETATION_FORBIDDEN=true
EXECUTION_ATTEMPT_LIMIT=1
HOST_EXECUTION_LEASE_WRITE_FORBIDDEN=true
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

## `QW-LC4-E`: one-shot host-runtime-invoker implementation

See [ADR-075](docs/decisions/ADR-075-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-implementation_EN.md).

After post-merge verification of PR #135, the bounded host invoker is implemented. It reinspects the image and canonical argv twice, creates at most one no-shell child in a separate process group, forwards signals, applies a terminal timeout, and bounds output. The verifier never calls the invoker, and tests use only a fake child process.

```text
qwake_adr=ADR-075-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-implementation
HOST_RUNTIME_INVOKER_IMPLEMENTATION_PRESENT=true
HOST_RUNTIME_INVOKER_PRESENT=true
HOST_RUNTIME_INVOKER_EXECUTABLE=true
HOST_DOCKER_RUN_IMPLEMENTED=true
PRELAUNCH_IMAGE_INSPECTION_COUNT=2
PRELAUNCH_MATERIALIZATION_COUNT=2
SUBPROCESS_POPEN_CALL_LIMIT=1
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

## `QW-LC4-E`: host-runtime-invoker repository freeze materialized

See [ADR-076](docs/decisions/ADR-076-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-repository-freeze_EN.md).

After independent verification of PR #136 merge, a two-file receipt now binds
the exact merge commit, both parents, the corrected hermetic test, implementation
hashes, and Torch2PC revision. This slice does not invoke the runner, inspect the
local image, or create a lease or output. The freeze remains incomplete until
receipt merge and reverification.

```text
qwake_adr=ADR-076-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-repository-freeze
qwake_host_runtime_invoker_repository_main_commit=da51c8d858c541372525125640db99062041fc20
qwake_host_runtime_invoker_implementation_head=181abda36465d3a91db5970e684938266200a798
qwake_host_runtime_invoker_repository_freeze_materialized=true
qwake_host_runtime_invoker_repository_freeze_complete=false
qwake_next_slice=QW-LC4-E-one-shot-host-runtime-invoker-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC4-E-one-shot-engineering-invocation
HOST_RUNTIME_INVOKER_IMPLEMENTATION_PRESENT=true
HOST_RUNTIME_INVOKER_PRESENT=true
HOST_RUNTIME_INVOKER_EXECUTABLE=true
HOST_DOCKER_RUN_IMPLEMENTED=true
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
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
IMAGE_INSPECTION_PERFORMED=false
DOCKER_RUN_PERFORMED=false
RUNTIME_RERUN_PERFORMED=false
FILES_STAGED=false
```

## `QW-LC4-E`: one-shot engineering invocation admission materialized

See [ADR-077](docs/decisions/ADR-077-stage3b-qwake-lc4-e-one-shot-engineering-invocation-admission_EN.md).

After independent verification of the PR #137 merge, a pure admission now binds
the exact repository freeze, the previously issued one-shot authorization, the
immutable image, and the bounded host invoker. Runtime inspection and the
invocation remain a separate operator operation; this slice performs no image
inspection, `docker run`, lease claim, or output write.

```text
qwake_adr=ADR-077-stage3b-qwake-lc4-e-one-shot-engineering-invocation-admission
qwake_invocation_base_commit=3454d12d3cc16c9c50977e2a598e2bc1a8768441
qwake_invocation_admission_sha256=sha256:fe07bc20bf5866d84730df945c2ababc7b5f4f255648c5de6e3185ba4e37c01d
REPOSITORY_FREEZE_COMPLETE=true
INVOCATION_ADMISSION_RECORD_PRESENT=true
PREEXECUTION_IDENTITY_CHECKS_IMPLEMENTED=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
IMAGE_INSPECTION_PERFORMED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: one-shot engineering invocation operation record materialized

See [ADR-078](docs/decisions/ADR-078-stage3b-qwake-lc4-e-one-shot-engineering-invocation-operation_EN.md).

After independent verification of the PR #138 merge, a pure operation record
now binds the admission merge commit, authorization, image, Torch2PC revision,
and bounded host invoker while freezing the exact dynamic checks for a future
spawn. This slice performs no image inspection, command materialization, lease
claim, or `docker run`.

```text
qwake_adr=ADR-078-stage3b-qwake-lc4-e-one-shot-engineering-invocation-operation
qwake_operation_base_commit=28be77706bc86abaf34f86e9bdcbdcb9cc2810a8
qwake_invocation_operation_sha256=sha256:10a612ef1b765362b361ecea57923d00a9f7339c9d3f9e3b27337f92f15326e9
REPOSITORY_FREEZE_COMPLETE=true
INVOCATION_ADMISSION_COMPLETE=true
INVOCATION_OPERATION_RECORD_PRESENT=true
PREEXECUTION_IDENTITY_CHECKS_IMPLEMENTED=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_OPERATION_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: one-shot engineering invocation execution authorization materialized

See [ADR-079](docs/decisions/ADR-079-stage3b-qwake-lc4-e-one-shot-engineering-invocation-execution-authorization_EN.md).

After independent verification of the PR #139 merge, a pure authorization now
binds the operation merge, previous one-shot authorization, image, Torch2PC
revision, and bounded host invoker while freezing mandatory same-process
pre-execution verification. The authoring branch performs no image inspection,
command materialization, lease creation, or `docker run`.

```text
qwake_adr=ADR-079-stage3b-qwake-lc4-e-one-shot-engineering-invocation-execution-authorization
qwake_execution_base_commit=b0f6729e8fd1cb1aa172eef488dc56e36b335173
qwake_execution_authorization_sha256=sha256:ff136538faee0d7952dc444e521d7ec760c7d54cd38406cb9b19ff1e00d9437b
REPOSITORY_FREEZE_COMPLETE=true
INVOCATION_ADMISSION_COMPLETE=true
INVOCATION_OPERATION_COMPLETE=true
EXECUTION_AUTHORIZATION_RECORD_PRESENT=true
EXECUTION_AUTHORIZATION_ISSUED=true
PREEXECUTION_VERIFICATION_MATERIALIZATION_IMPLEMENTED=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_OPERATION_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_EXECUTION_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: pre-execution contract for the one-shot engineering invocation materialized

See [ADR-080](docs/decisions/ADR-080-stage3b-qwake-lc4-e-one-shot-engineering-invocation-preexecution-verification_EN.md).

After independent verification of the PR #140 merge, a pure pre-execution
contract was materialized. It binds the authorization merge commit to the exact
host-invoker implementation and records that both image inspections, both
command materializations, and the single child creation belong to one future
call. The current branch performs no dynamic image verification, command
materialization, lease creation, or `docker run`.

```text
qwake_adr=ADR-080-stage3b-qwake-lc4-e-one-shot-engineering-invocation-preexecution-verification
qwake_preexecution_base_commit=49c4b97e93b47cefbf35576736927ece02c9402b
qwake_preexecution_verification_sha256=sha256:833371b427a5c8a6e602d675711b85b2edc68441b9e5be191321a2911bce6128
INVOCATION_OPERATION_COMPLETE=true
EXECUTION_AUTHORIZATION_COMPLETE=true
PREEXECUTION_VERIFICATION_RECORD_PRESENT=true
PREEXECUTION_VERIFIER_IMPLEMENTED=true
PREEXECUTION_STATIC_CONTRACT_VERIFIED=true
PREEXECUTION_VERIFICATION_SLICE_OPEN=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_EXECUTION_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_OPEN=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: bounded one-shot engineering invocation runtime operation materialized

See [ADR-081](docs/decisions/ADR-081-stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation_EN.md).

After independent verification of the PR #141 merge, a pure atomic-operation
contract and bounded entry point are materialized. It requires explicit
permission, exact acknowledgement, a post-merge claim time, the previous
authorization acknowledgement, and the complete host-resource set. Dynamic
verification and the sole spawn are delegated to the existing host invoker;
the authoring branch does not inspect the image, materialize a command, create
a lease, or invoke Docker.

```text
qwake_adr=ADR-081-stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation
qwake_runtime_operation_base_commit=494e6a0b2f10c26b49c90fbb84c23565699a4064
qwake_runtime_operation_sha256=sha256:0332428014f7f8385c789ba7e7c55d6c2ec03b020e3f83df9ac9714483bb6bf8
EXECUTION_AUTHORIZATION_COMPLETE=true
PREEXECUTION_VERIFICATION_COMPLETE=true
PREEXECUTION_STATIC_CONTRACT_VERIFIED=true
RUNTIME_OPERATION_RECORD_PRESENT=true
RUNTIME_OPERATION_EXECUTOR_ENTRYPOINT_IMPLEMENTED=true
RUNTIME_OPERATION_STATIC_CONTRACT_VERIFIED=true
ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_OPEN=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## QW-LC4-E: runtime-operation identity repair

- PR #142 was merged into `main` as `97dacb207aa201f1fd2f43c66ae34b1adced32bb`;
- the historical ADR-081 retained the pre-Ruff module SHA while its two-file package did not bind executable source;
- ADR-082 adds a non-retroactive identity-repair package and mandatory runtime-operation verifier self-identity verification;
- historical ADR-081 and package v1 are not rewritten;
- execution remains blocked pending corrected validation, repair merge, persistent lease v2, and a durable negative host outcome;
- `ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false`, `DOCKER_RUN_PERFORMED=false`.

## `QW-LC4-E`: persistent evidence chain v2 materialized as an authoring contract

See [ADR-083](docs/decisions/ADR-083-stage3b-qwake-lc4-e-persistent-evidence-chain-v2_EN.md).

PR #143 was merged as `5e61ed650c9beda2cde1f58650345f01694836f6` and
independently verified with `24` focused, `201` targeted, and `1248` full tests.
The authoring package binds the complete current authorization and operation
chain into a persistent lease-v2 template and defines a mandatory durable
terminal host-outcome receipt. Persistence and lease-bound wiring are not yet
implemented; execution remains closed.

```text
qwake_adr=ADR-083-stage3b-qwake-lc4-e-persistent-evidence-chain-v2
qwake_persistent_evidence_chain_v2_base=5e61ed650c9beda2cde1f58650345f01694836f6
qwake_persistent_evidence_chain_v2_sha256=sha256:c0a6195080cec64e6104a90076366cc2bfa10a723b45a7389cd77fa1b3b11bd1
CORRECTED_FULL_VALIDATION_RECEIPT_PRESENT=true
RUNTIME_OPERATION_IDENTITY_REPAIR_MERGED=true
LATEST_AUTHORIZATION_BOUND_IN_PERSISTENT_LEASE_TEMPLATE=true
DURABLE_NEGATIVE_HOST_OUTCOME_DEFINED=true
PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=false
DURABLE_OUTCOME_WRITER_IMPLEMENTED=false
LEASE_BOUND_HOST_INVOKER_ENFORCED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: persistent evidence chain v2 writers implemented

See [ADR-084](docs/decisions/ADR-084-stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation_EN.md).

From PR #144 merge `3d092440b0314f02072c9773cc91018bf2860744`,
fail-closed writers now implement the persistent lease v2 and durable terminal
host outcome. The implementation provides exclusive no-overwrite, mode `0600`,
file/directory `fsync`, symbolic-parent rejection, temporary cleanup, and exact
canonical lease-byte verification before outcome persistence. Host-invoker
wiring and execution remain closed.

```text
PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=true
DURABLE_OUTCOME_WRITER_IMPLEMENTED=true
LEASE_BOUND_HOST_INVOKER_ENFORCED=false
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
FILES_STAGED=false
```

## `QW-LC4-E`: host invoker bound to persistent lease v2

See [ADR-085](docs/decisions/ADR-085-stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring_EN.md). The prospective entry point verifies exact persisted lease-v2 bytes before delegation, forbids retry, and writes a durable terminal receipt. The historical direct operation remains unchanged but is superseded for future authorization.

```text
LEASE_BOUND_HOST_INVOKER_ENFORCED=true
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_EXECUTION_PERFORMED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: final execution acknowledgement authoring

See [ADR-086](docs/decisions/ADR-086-stage3b-qwake-lc4-e-final-execution-acknowledgement-authoring_EN.md).

After independent verification of PR #146 merged as
`2957d8f6975c88e7bdb23243e3915c7f51d4ba47`, a separate static authoring
package binds evidence chain v2, its implementation, the lease-bound invoker,
authorizations, exact image, Torch2PC, output root, and
`invocation_count=1`. A future acknowledgement requires the exact phrase
`ACKNOWLEDGE_QWAKE_LC4_FINAL_ONE_SHOT_EXECUTION`, operator identity, and a UTC
time after merge. The package does not issue the acknowledgement or transition
to lease materialization or invocation.

```text
qwake_adr=ADR-086-stage3b-qwake-lc4-e-final-execution-acknowledgement-authoring
qwake_acknowledgement_authoring_base=2957d8f6975c88e7bdb23243e3915c7f51d4ba47
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

See [ADR-087](docs/decisions/ADR-087-stage3b-qwake-lc4-e-final-execution-acknowledgement-issuance-authoring_EN.md).

After independent verification of PR #147 merged as
`eb20c157584efff8e9aa0418385242c7d7b26eab`, the static issuance contract
binds the exact ADR-086 package to the sole future acknowledgement path, the
operator, issuer, two UTC timestamps, and atomic no-overwrite persistence. The
writer and acknowledgement remain absent; lease and execution stay closed.

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


## `QW-LC4-E`: final acknowledgement issuance implementation

See [ADR-088](docs/decisions/ADR-088-stage3b-qwake-lc4-e-final-execution-acknowledgement-issuance-implementation_EN.md).

After independent verification of PR #148 merged as
`8343724c66b1d22f01846d9fc70f01738a09127a`, an atomic writer for the canonical
final-acknowledgement envelope is implemented. It enforces no-overwrite, mode
`0600`, `fsync`, symbolic-parent rejection, and exact-byte reverification. No
production callsite or acknowledgement file exists; execution remains closed.

```text
issuance_authoring_pr=148
issuance_authoring_focused_tests=61
issuance_authoring_targeted_tests=262
issuance_authoring_full_tests=1309
issuance_authoring_full_test_warnings=14
ACKNOWLEDGEMENT_ISSUANCE_AUTHORING_POST_MERGE_VERIFIED=true
ACKNOWLEDGEMENT_ISSUANCE_CONTRACT_AUTHORED=true
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


## `QW-LC4-E`: final acknowledgement materialization authoring

See [ADR-089](docs/decisions/ADR-089-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-authoring_EN.md).

After independent verification of PR #149 merged as
`31206012ef7cbd2b7b21a2017374c11123abd42c`, a static operator-bound contract
for the future materialization is frozen. It binds the exact writer
implementation, operator phrase, operator/issuer/materializer identities,
ordered timestamps, target path, and canonical SHA-256. The acknowledgement
file and production callsite remain absent; execution stays closed.

```text
issuance_implementation_pr=149
issuance_implementation_focused_tests=79
issuance_implementation_targeted_tests=280
issuance_implementation_full_tests=1327
issuance_implementation_full_test_warnings=14
ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTATION_POST_MERGE_VERIFIED=true
ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTED=true
ACKNOWLEDGEMENT_MATERIALIZATION_CONTRACT_AUTHORED=true
ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTED=false
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


## `QW-LC4-E`: final acknowledgement materialization implementation

See [ADR-090](docs/decisions/ADR-090-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-implementation_EN.md).

After independent verification of PR #150 merged as
`6497cd904f9403622249c5a32f08ef6e8bb11532`, a narrow materializer is
implemented. On a future explicit call it accepts only the exact prospective
materialization, delegates one atomic writer call, and performs one exact
persisted-byte reverification. The materializer is not called in this branch;
the production acknowledgement and runtime artifacts remain absent.

```text
materialization_authoring_pr=150
materialization_authoring_focused_tests=92
materialization_authoring_targeted_tests=293
materialization_authoring_full_tests=1340
materialization_authoring_full_test_warnings=14
MATERIALIZATION_AUTHORING_POST_MERGE_VERIFIED=true
ACKNOWLEDGEMENT_MATERIALIZATION_CONTRACT_AUTHORED=true
ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTED=true
MATERIALIZER_CALLED=false
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

## `QW-LC4-E`: final-acknowledgement materializer invocation authoring

See [ADR-091](docs/decisions/ADR-091-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-authoring_EN.md).

After independent verification of PR #151 merged as
`7d5e5058af6a845cf4a6add2e7fe199894f48b24`, a pure contract for the sole
future materializer call is frozen. It requires exact operator-bound inputs, one
materializer call, no direct writer call, and durable-state inspection before
recovery. Automatic and blind retry are forbidden, while explicit recovery is
allowed after state classification. No actual call or acknowledgement exists.

```text
materialization_implementation_pr=151
materialization_implementation_focused_tests=108
materialization_implementation_targeted_tests=309
materialization_implementation_full_tests=1356
materialization_implementation_full_test_warnings=14
MATERIALIZATION_IMPLEMENTATION_POST_MERGE_VERIFIED=true
ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTED=true
MATERIALIZATION_INVOCATION_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_IMPLEMENTED=false
MATERIALIZATION_INVOKED=false
MATERIALIZER_CALLED=false
WRITER_CALLED=false
AUTOMATIC_RETRY_FORBIDDEN=true
BLIND_RETRY_FORBIDDEN=true
EXPLICIT_RECOVERY_PERMITTED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## `QW-LC4-E`: final-acknowledgement materialization invocation implementation

See [ADR-092](docs/decisions/ADR-092-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-implementation_EN.md).

After independent verification of PR #152 merged as
`febfba65d2f200fd2163928643eadd807a6b4d21`, a bounded library adapter is
implemented. It classifies durable state first, delegates at most one
materializer call when the target is absent, treats a valid existing target as
completed without another call, and rejects an invalid target. No production
callsite or acknowledgement exists.

```text
invocation_authoring_pr=152
invocation_authoring_focused_tests=124
invocation_authoring_targeted_tests=325
invocation_authoring_full_tests=1372
invocation_authoring_full_test_warnings=14
ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_AUTHORING_POST_MERGE_VERIFIED=true
MATERIALIZATION_INVOCATION_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_IMPLEMENTED=true
MATERIALIZATION_INVOKED=false
MATERIALIZER_CALLED=false
WRITER_CALLED=false
AUTOMATIC_RETRY_FORBIDDEN=true
BLIND_RETRY_FORBIDDEN=true
EXPLICIT_RECOVERY_PERMITTED=true
RECOVERY_STATE_PROBE_REQUIRED=true
VALID_EXISTING_TARGET_TREATED_AS_SUCCESS=true
INVALID_EXISTING_TARGET_FAIL_CLOSED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
EXECUTION_LEASE_MATERIALIZED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## `QW-LC4-E`: operator-operation authoring for acknowledgement materialization invocation

See [ADR-093](docs/decisions/ADR-093-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-authoring_EN.md).

After independent verification of PR #153 merged as
`0ace9f1025100fa29ff0af7523fde17674c4852b`, a pure future operator-operation
contract is frozen. A distinct operation phrase is bound to the exact prospective
invocation and operator identity. A future implementation may call only the
library adapter and at most once; standalone pre-probing and direct materializer
or writer calls are forbidden. No operation or acknowledgement exists.

```text
invocation_implementation_pr=153
invocation_implementation_focused_tests=144
invocation_implementation_targeted_tests=345
invocation_implementation_full_tests=1392
invocation_implementation_full_test_warnings=14
ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_IMPLEMENTATION_POST_MERGE_VERIFIED=true
MATERIALIZATION_INVOCATION_IMPLEMENTED=true
MATERIALIZATION_INVOCATION_OPERATION_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTED=false
MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false
INVOCATION_ADAPTER_CALLED=false
MATERIALIZATION_INVOKED=false
MATERIALIZER_CALLED=false
WRITER_CALLED=false
ADAPTER_OWNED_RECOVERY_PROBE_REQUIRED=true
STANDALONE_PREPROBE_FORBIDDEN=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
EXECUTION_LEASE_MATERIALIZED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```


## `QW-LC4-E`: acknowledgement-materialization invocation operator-operation implementation

See [ADR-094](docs/decisions/ADR-094-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-implementation_EN.md).

After independent verification of PR #154 merged as
`5ee6d2346e558be19cfdf79e8a77b0568475bf4c`, a bounded library operation is
implemented. It validates the exact prospective operation and delegates exactly
once to the existing adapter. No standalone pre-probe, direct materializer or
writer call, production callsite, or actual operation exists.

```text
operation_authoring_pr=154
operation_authoring_focused_tests=162
operation_authoring_targeted_tests=363
operation_authoring_full_tests=1410
operation_authoring_full_test_warnings=14
ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_AUTHORING_POST_MERGE_VERIFIED=true
MATERIALIZATION_INVOCATION_OPERATION_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTED=true
MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false
INVOCATION_ADAPTER_CALLED=false
ADAPTER_CALL_LIMIT=1
STANDALONE_PREPROBE_FORBIDDEN=true
DIRECT_MATERIALIZER_CALL_FORBIDDEN=true
DIRECT_WRITER_CALL_FORBIDDEN=true
PRODUCTION_CALLSITE_PRESENT=false
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
EXECUTION_LEASE_MATERIALIZED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```


## `QW-LC4-E`: production-callsite authoring for the operator operation

See [ADR-095](docs/decisions/ADR-095-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-callsite-authoring_EN.md).

After independent verification of PR #155 merged as
`23a86cc0769f20b4b7536e64250f3dee062aaa62`, the future production-callsite
contract is frozen. Its path, CLI inputs, and single library delegate are exact.
The callsite file remains absent; the operation, adapter, materializer, and writer
are not called.

```text
operation_implementation_pr=155
operation_implementation_focused_tests=180
operation_implementation_targeted_tests=381
operation_implementation_full_tests=1428
operation_implementation_full_test_warnings=14
ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTATION_POST_MERGE_VERIFIED=true
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_IMPLEMENTED=false
PRODUCTION_CALLSITE_PRESENT=false
MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false
INVOCATION_ADAPTER_CALLED=false
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
EXECUTION_LEASE_MATERIALIZED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## `QW-LC4-E`: production-callsite implementation for the operator operation

See [ADR-096](docs/decisions/ADR-096-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-callsite-implementation_EN.md).

After reconciliation of PR #162 merged as
`b27e252cf7c64e88d5d61bf7a23c70ffc5957959`, the exact command interface is
implemented with required `--project-root` and `--operation-json` inputs. It
accepts only a canonical operation file, delegates exactly once to the library
operation, and emits only a verified canonical result. It was not executed in
the primary worktree.

```text
callsite_authoring_pr=162
callsite_authoring_actual_first_parent=dc8dc200515959858d43b68984dbd87f27f3446c
callsite_authoring_merge=b27e252cf7c64e88d5d61bf7a23c70ffc5957959
callsite_authoring_first_parent_files=18
callsite_authoring_first_parent_insertions=1516
callsite_authoring_first_parent_deletions=0
ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_AUTHORING_POST_MERGE_VERIFIED=true
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_IMPLEMENTED=true
PRODUCTION_CALLSITE_PRESENT=true
MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false
INVOCATION_ADAPTER_CALLED=false
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
EXECUTION_LEASE_MATERIALIZED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```



## `QW-LC4-E`: production-callsite execution contract

See [ADR-097](docs/decisions/ADR-097-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-callsite-execution-authoring_EN.md).

After independent verification of PR #163 merged as `78129528d05e8268b4e40fdf708fd9d2c8e3ab29`, the contract for one future production-callsite execution is frozen. Authorization and `operation.json` remain separate and absent; the callsite is not executed.

```text
callsite_implementation_pr=163
callsite_implementation_focused_tests=219
callsite_implementation_targeted_tests=420
callsite_implementation_full_tests=1467
callsite_implementation_full_test_warnings=14
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_AUTHORIZED=false
PRODUCTION_CALLSITE_PRESENT=true
PRODUCTION_CALLSITE_EXECUTED=false
MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## `QW-LC4-E`: production-callsite execution authorization

See [ADR-098](docs/decisions/ADR-098-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-callsite-execution-authorization_EN.md).

After independent verification of PR #164 merged as `75936adac9ee100f9538f5af13a8ce312642ee0b`, a separate single-use authorization record and canonical `operation.json` are materialized. The record is bound to the operator, exact callsite, and input SHA-256, but it is not effective until this slice is independently verified after merge. The production callsite was not executed.

```text
execution_authoring_pr=164
execution_authoring_focused_tests=240
execution_authoring_targeted_tests=441
execution_authoring_full_tests=1488
execution_authoring_full_test_warnings=14
EXECUTION_AUTHORIZATION_RECORD_PRESENT=true
EXECUTION_AUTHORIZATION_ISSUED=true
CANONICAL_OPERATION_JSON_MATERIALIZED=true
EXECUTION_AUTHORIZATION_POST_MERGE_VERIFIED=false
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_AUTHORIZED=false
PRODUCTION_CALLSITE_EXECUTED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## `QW-LC4-E`: transition after final-acknowledgement materialization

See [ADR-099](docs/decisions/ADR-099-stage3b-qwake-lc4-e-post-acknowledgement-transition_EN.md).

The one-shot production callsite for final-acknowledgement materialization is
complete. Its authorization is consumed, the acknowledgement is issued and
verified, and retry is forbidden. No persistent lease v2, terminal host receipt,
or runtime output exists. This evidence package is therefore not the successful
extension engineering report and does not open `QW-5`.

```text
QW_LC4_E_ACKNOWLEDGEMENT_LINE_COMPLETE=true
QW_LC4_E_ACKNOWLEDGEMENT_AUTHORIZATION_CONSUMED=true
QW_LC4_E_ACKNOWLEDGEMENT_RETRY_PERMITTED=false
QW_LC4_E_ACKNOWLEDGEMENT_REINVOCATION_FORBIDDEN=true
QW_LC4_E_EXTENSION_ENGINEERING_REPORT_PRESENT=false
QW_LC4_E_COMPLETE=false
QW5_TRANSITION_PERMITTED=false
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-admission-authoring
```

## `QW-LC4-E`: final engineering-invocation admission-authoring scope freeze

See [ADR-100](docs/decisions/ADR-100-stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-scope-freeze_EN.md).

The exact source identities, sole prospective
`invoke_lease_bound_host_runtime` entry point, requirement for a new distinct
one-shot authorization, and future admission-authoring acceptance criteria are
frozen. No admission schema, verifier, admission record, or authorization
exists yet. No lease v2, durable host outcome, or runtime output was created.

```text
FINAL_ENGINEERING_INVOCATION_ADMISSION_AUTHORING_SCOPE_FROZEN=true
FINAL_ENGINEERING_INVOCATION_ADMISSION_AUTHORED=false
FINAL_ENGINEERING_INVOCATION_ADMISSION_RECORD_PRESENT=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=false
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
EXTENSION_ENGINEERING_REPORT_PRESENT=false
QW_LC4_E_COMPLETE=false
QW5_TRANSITION_PERMITTED=false
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-admission-authoring-scope-freeze-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-admission-authoring
```

## `QW-LC4-E`: final engineering-invocation admission authoring

See [ADR-101](docs/decisions/ADR-101-stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring_EN.md).

A pure schema, verifier, temporary-directory negative tests, and canonical
admission record are materialized. The record binds exact source identities and
the future `invoke_lease_bound_host_runtime` entrypoint, but it is not an
authorization and does not permit invocation.

```text
FINAL_ENGINEERING_INVOCATION_ADMISSION_AUTHORING_SCOPE_FROZEN=true
FINAL_ENGINEERING_INVOCATION_ADMISSION_AUTHORED=true
FINAL_ENGINEERING_INVOCATION_ADMISSION_RECORD_PRESENT=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=false
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
EXTENSION_ENGINEERING_REPORT_PRESENT=false
QW_LC4_E_COMPLETE=false
QW5_TRANSITION_PERMITTED=false
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-admission-authoring-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-admission-repository-seal
```

## `QW-LC4-E`: final engineering-invocation admission repository seal materialized

See [ADR-102](docs/decisions/ADR-102-stage3b-qwake-lc4-e-final-engineering-invocation-admission-repository-seal_EN.md).

After independent verification of PR #169, the admission record is bound to
exact `main` `d2539eb440e758c1f29b935f8599561bec7126bc`, both PR commits, the 17-file scope, and exact artifact
SHA-256 identities. The two-file repository receipt is materialized but becomes
complete only after its own merge and independent post-merge verification. No
new authorization exists, and even its separate authoring is not yet permitted.

```text
FINAL_ENGINEERING_INVOCATION_ADMISSION_PR=169
FINAL_ENGINEERING_INVOCATION_ADMISSION_PR_HEAD=b81c11971f1e9b78e59dd39c4d182722a3001044
FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_MAIN_COMMIT=d2539eb440e758c1f29b935f8599561bec7126bc
FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_SEAL_MATERIALIZED=true
FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_SEAL_COMPLETE=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORING_PERMITTED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=false
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
EXTENSION_ENGINEERING_REPORT_PRESENT=false
QW_LC4_E_COMPLETE=false
QW5_TRANSITION_PERMITTED=false
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-admission-repository-seal-merge
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-authoring
```

## `QW-LC4-E`: new one-shot authorization-authoring scope freeze

See [ADR-103](docs/decisions/ADR-103-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-authoring-scope-freeze_EN.md).

After PR #170 merge and independent verification, the admission repository seal
is complete for exact `main`
`a5b96edb1f82485561e0f52d6a98432d55ae8609`. Only exact inputs, future
authoring surfaces, and one-shot semantics for a distinct new authorization are
frozen. The schema, verifier, tests, authorization record, and operator phrase
remain absent. This slice neither permits invocation nor creates runtime
artifacts.


The verifiable record does not change the actual compute-environment state. It
only binds input provenance, operator identity, a separate verbal
acknowledgement, and the strict ordering of a future action. Before separate
merge verification, every attempt to treat the record as effective authority
must fail closed. Repository state remains the sole verifiable source of truth
about record issuance, while the operational environment receives no new
files, processes, or results.

```text
FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_SEAL_COMPLETE=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORING_SCOPE_FROZEN=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_RECORD_PRESENT=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=false
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
OPERATOR_PHRASE_RESERVED=false
INVOCATION_COMMAND_MATERIALIZED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
EXTENSION_ENGINEERING_REPORT_PRESENT=false
QW_LC4_E_COMPLETE=false
QW5_TRANSITION_PERMITTED=false
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-authoring-scope-freeze-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-record-authoring
```

## 2026-08-03 — author the new one-shot final engineering-invocation authorization

- added [ADR-104](docs/decisions/ADR-104-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-record-authoring_EN.md);
- after independent verification of PR #171 merged as `61f190db2fbd4bf0ee8a58cac8b6841fbecc6cdd`, materialized a pure schema, verifier, tests, and canonical distinct one-shot authorization record;
- the record binds operator `local-posix-account:dzmitry-prychyna` and separate phrase `AUTHORIZE_QWAKE_LC4_FINAL_ENGINEERING_INVOCATION_ONCE_AFTER_POST_MERGE_VERIFICATION`;
- the record is issued but creates no effective invocation authority before its own merge and independent post-merge verification;
- the new record is distinct from every historical authorization and serves only as a verifiable repository basis for a future one-shot operator action;
- current authoring keeps the complete operational boundary closed: it starts no attempt, changes no lease state, and creates no observable result;
- command, consumption, lease v2, durable host outcome, runtime output, and `QW-5` remain absent.

```text
FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_SEAL_COMPLETE=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORING_SCOPE_FREEZE_COMPLETE=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_RECORD_PRESENT=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=false
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
OPERATOR_PHRASE_RESERVED=true
INVOCATION_COMMAND_MATERIALIZED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
EXTENSION_ENGINEERING_REPORT_PRESENT=false
QW_LC4_E_COMPLETE=false
QW5_TRANSITION_PERMITTED=false
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-record-authoring-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-scope-freeze
```

## `QW-LC4-E`: authorization consumption-attempt scope freeze

See [ADR-105](docs/decisions/ADR-105-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-scope-freeze_EN.md).

After PR #172 merge and independent verification, the one-shot authorization is
post-merge verified and effective for exact `main`
`47bb24dc8fa95292be33428ba8bc7ee598c49b1e`, but remains unconsumed. This slice
freezes only the inputs, future surfaces, and atomic semantics for preparing one
consumption attempt. It creates no attempt record, starts no attempt, and
creates no persistent lease v2.

Future attempt-record preparation must remain non-executing. Only after its own
merge and independent verification may a separate operational action atomically
consume the authorization, start the attempt, and exclusively create durable
lease v2 before calling `invoke_lease_bound_host_runtime`.

```text
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_RECORD_LINE_COMPLETE=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=true
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_SCOPE_FROZEN=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_PRESENT=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_STARTED=false
INVOCATION_COMMAND_MATERIALIZED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
EXTENSION_ENGINEERING_REPORT_PRESENT=false
QW_LC4_E_COMPLETE=false
QW5_TRANSITION_PERMITTED=false
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-scope-freeze-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-record-authoring
```

## `QW-LC4-E`: prepared authorization-consumption attempt record

See [ADR-106](docs/decisions/ADR-106-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-record-authoring_EN.md).

After PR #173 merge and independent verification, the ADR-105 scope freeze is
complete for exact `main` `28b4627436244893195231f55f2d0d5fb2d1062e`. A pure
schema, verifier, tests, and distinct canonical attempt record are materialized.
The record is prepared but grants no atomic-action authority before its own
merge and independent verification.

Authorization remains effective and unconsumed. The attempt is not started;
the command, lease v2, durable host outcome, and [runtime](docs/glossary_EN.md#term-runtime) output are absent.

```text
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_RECORD_LINE_COMPLETE=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=true
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_SCOPE_FROZEN=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_SCOPE_FREEZE_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_AUTHORING_ADMISSIBLE=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_AUTHORED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_STARTED=false
INVOCATION_COMMAND_MATERIALIZED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
EXTENSION_ENGINEERING_REPORT_PRESENT=false
QW_LC4_E_COMPLETE=false
QW5_TRANSITION_PERMITTED=false
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-record-authoring-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-scope-freeze
```

## `QW-LC4-E`: atomic authorization-consumption transition scope freeze

See [ADR-107](docs/decisions/ADR-107-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-scope-freeze_EN.md).

After independent verification of PR #174, the prepared attempt record is
post-merge verified. ADR-107 freezes the sole future commit object: the exact
durable lease-v2 file. Authorization consumption and attempt start are derived
from atomic no-replace creation of its fully prepared canonical bytes.

This slice only freezes scope. It creates no transition implementation, consumes
no authorization, starts no attempt, creates no lease, and invokes no runtime.

```text
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_RECORD_LINE_COMPLETE=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=true
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_SCOPE_FROZEN=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_SCOPE_FREEZE_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_FROZEN=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_FREEZE_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_AUTHORING_ADMISSIBLE=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_AUTHORED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_COMMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_STARTED=false
INVOCATION_COMMAND_MATERIALIZED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
EXTENSION_ENGINEERING_REPORT_PRESENT=false
QW_LC4_E_COMPLETE=false
QW5_TRANSITION_PERMITTED=false
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-scope-freeze-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-authoring
```

## QW-LC4-E: authorization-consumption atomic-transition authoring (ADR-108)

ADR-107 and PR #175 are post-merge verified at `c9958638a17802cd293c5fa79fd6074c226a85ef`. The module, verifier, tests, and immutable transition record are authored. The entrypoint exists but the authoring verifier does not call it, and the runtime invoker is not imported. The operational effect remains closed pending a separate operation-scope freeze after ADR-108 merge and independent verification.

```text
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_FROZEN=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_FREEZE_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_AUTHORING_ADMISSIBLE=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_AUTHORED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_FREEZE_ADMISSIBLE=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_COMMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_STARTED=false
INVOCATION_COMMAND_MATERIALIZED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
QW5_TRANSITION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
```

## `QW-LC4-E`: atomic-transition operation scope freeze (ADR-109)

After independent verification of PR #176, the ADR-108 transition is post-merge verified. [ADR-109](docs/decisions/ADR-109-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-scope-freeze_EN.md) freezes the exact admission, preflight order, sole future call, and failure states for a separate operator operation.

This slice creates only immutable scope. It does not invoke the atomic transition or writer, consume authorization, start the attempt, or create lease v2.

```text
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=true
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_FREEZE_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_AUTHORED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_FREEZE_ADMISSIBLE=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_FROZEN=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_FREEZE_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_AUTHORING_ADMISSIBLE=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_AUTHORED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_COMMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_STARTED=false
INVOCATION_COMMAND_MATERIALIZED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
QW5_TRANSITION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-scope-freeze-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-authoring
```

## `QW-LC4-E`: combined one-shot atomic-transition operation authoring (ADR-110)

After independent verification of PR #177 merged as `e33448d10ced2bffd1e48449e6da46b2de938141`, the ADR-109 scope is post-merge verified. [ADR-110](docs/decisions/ADR-110-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-authoring_EN.md) combines the operation module, immutable record, embedded admission contract, verifier, and tests in one non-executing slice.

At the ADR-110 authoring checkpoint, the wrapper existed but had not yet been invoked. The block below records that historical pre-execution state; the actual terminal outcome of attempt 001 and the current state are defined by the later ADR-111 section.

```text
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=true
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_FROZEN=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_FREEZE_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_AUTHORING_ADMISSIBLE=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_AUTHORED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_MODULE_CREATED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_VERIFIER_CREATED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_TESTS_CREATED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_RECORD_PRESENT=true
COMBINED_OPERATION_ADMISSION_CONTRACT_CREATED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_COMMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_STARTED=false
INVOCATION_COMMAND_MATERIALIZED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
QW5_TRANSITION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-execution
```


## `QW-LC4-E`: terminal attempt 001 and claim/execute correction (ADR-111)

Attempt 001 ended with `nonzero_return_code=1` after one child spawn. Lease v1, lease v2, and the durable host receipt are preserved; retry is forbidden. The defect is localized to a repeated pre-claim admission check after the successful lease-v1 claim.

ADR-111 preserves historical source identities and adds an immutable correction overlay. The corrected entrypoint carries one `FrozenAdmissionIdentity` through build, atomic materialization, and the claimed wrapper without a post-claim unconsumed-state check. The corrected image and attempt 002 are not yet materialized; runtime and `QW-5` remain closed.

```text
ATTEMPT_001_TERMINAL=true
ATTEMPT_001_TERMINATION_CLASS=nonzero_return_code
ATTEMPT_001_RETURN_CODE=1
ATTEMPT_001_RETRY_PERMITTED=false
ATTEMPT_001_TERMINAL_RECEIPT_VERIFIED=true
HISTORICAL_FROZEN_SOURCE_MODIFIED=false
CLAIM_EXECUTE_ORDER_CORRECTION_AUTHORED=true
CORRECTED_IMAGE_BUILT=false
ATTEMPT_002_AUTHORIZED=false
RUNTIME_EXECUTION_PERFORMED=false
QW5_TRANSITION_PERMITTED=false
NEXT_SLICE=QW-LC4-E-claim-execute-order-correction-image-and-attempt-002-materialization
```


## `QW-LC4-E`: Attempt-005 terminal PASS and transition to `QW-5` (ADR-122)

Attempt-005 executed exactly once from canonical `main` `7168d6ebf3fbc27f5b85e1e44a7e8252f28038b0`. The
single engineering report has `validation_passed=true`: 168 measured cells, 28
reserve probes, 14 aggregates, CPU `7/7`, ROCm `7/7`, and zero order-effect
failures. No automatic retry was performed and rerun is forbidden.

ADR-122 binds the terminal evidence and completes `QW-LC4-E`. Only the next
preregistered `QW-5` scientific-image-freeze boundary is opened; the scientific
image itself is not materialized yet. `C1/C2/C3/R`, test-data access, and
publication remain closed.

```text
ATTEMPT_005_TERMINAL=true
ATTEMPT_005_VALIDATION_PASSED=true
ATTEMPT_005_RETRY_PERMITTED=false
ATTEMPT_005_AUTHORIZED_CELL_COUNT=168
ATTEMPT_005_RESERVE_PROBE_COUNT=28
ATTEMPT_005_AGGREGATE_COUNT=14
ATTEMPT_005_CPU_ORDER_EFFECT_PASS_COUNT=7
ATTEMPT_005_ROCM_ORDER_EFFECT_PASS_COUNT=7
ATTEMPT_005_ORDER_EFFECT_FAILURE_COUNT=0
QW_LC4_E_COMPLETE=true
QW5_TRANSITION_PERMITTED=true
QW5_OPEN=true
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=true
QW5_IMAGE_FROZEN=false
SCIENTIFIC_EXECUTION_OPEN=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
RUNTIME_RERUN_PERFORMED=false
NEXT_SLICE=QW-5-scientific-image-freeze
```


## `QW-5`: single scientific image frozen (ADR-123)

`QW-5` is complete through a separately proven corrective freeze of immutable
image `sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3`. Original `Attempt-001` remains a terminal failure:
`success=false`, `reinterpreted=false`, `retry_performed=false`. The same image
digest is mandatory across `C1/C2/C3/R`; C1 is not open yet.

```text
QW5_IMAGE_FROZEN=true
QW5_FREEZE_MODE=corrective_evidence
QW5_IMAGE_DIGEST=sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3
QW5_CORRECTIVE_FREEZE_SHA256=sha256:b435c09c02783f09156cfb7f68045151aa659e144e3c95d85480cee99020f6f4
ATTEMPT001_TERMINAL=true
ATTEMPT001_SUCCESS=false
ATTEMPT001_REINTERPRETED=false
EXECUTION_IMAGE_STRATEGY=single_immutable_superset_image
SAME_IMAGE_DIGEST_REQUIRED_ACROSS_C1_C2_C3_R=true
EXECUTABLE_CODE_CHANGES_AFTER_IMAGE_FREEZE=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=C1-request-freeze-and-authorization
```


## `QW-5`: superseding scientific orchestrator authored (ADR-124)

The structural C1-readiness audit found that the ADR-123 image contains the
closed capability model and scientific components but no preregistered
scientific-campaign entrypoint. The version-1 image and its corrective freeze
remain immutable.

ADR-124 adds source only for the generic host and embedded orchestrator, closed
canonical requests and authorizations, one-shot host claiming, and exact receipt
binding. No new image is built in this slice; `C1/C2/C3/R`, scientific
execution, test-dataset access, and publication remain closed.

```text
QW5_V1_PRESERVED=true
QW5_V1_IMAGE_DIGEST=sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3
QW5_V1_CORRECTIVE_FREEZE_SHA256=sha256:b435c09c02783f09156cfb7f68045151aa659e144e3c95d85480cee99020f6f4
C1_READINESS_AUDIT_V3_SHA256=sha256:c521e6992d5d9dbf2e0c8acdde4482d1b0ead82b1b4d8af0fcd1d2b3d0e1b5e2
SUPERSEDING_ORCHESTRATOR_AUTHORED=true
SUPERSEDING_QW5_IMAGE_BUILT=false
SUPERSEDING_QW5_IMAGE_FROZEN=false
C1_REQUEST_FROZEN=false
C1_EXECUTION_AUTHORIZATION_ISSUED=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=merge-post-merge-verify-then-superseding-image-build-and-freeze
```

## `QW-5`: superseding scientific image frozen and independently verified (ADR-125)

After ADR-124, the superseding image was built exactly once from merged source
`95a0bf35c87f87ee836596c02ab90a71703714f3` and independently verified. ADR-125 integrates
the unchanged freeze evidence into the repository. Historical QW-5 v1 remains
preserved, while the new digest becomes the operational image for future
`C1/C2/C3/R`.

```text
QW5_V1_HISTORICAL_FREEZE_PRESERVED=true
SUPERSEDING_QW5_IMAGE_DIGEST=sha256:7aefbc241ad725f4ac31d8b72c63a82247516ad4831aad6f7d0ef89817f9dacb
SUPERSEDING_QW5_FREEZE_SHA256=sha256:47c20698ac57c1b50f4bbe0314649b0d07494ecc1199b32819ecde7b684d9904
SUPERSEDING_IMAGE_FREEZE_INDEPENDENTLY_VERIFIED=true
REPOSITORY_INTEGRATION_SHA256=sha256:e35d1c90c3dc118c3a1514a62c7487196c48482de4cb1aae74e9ba942b2b518c
C1_REQUEST_FROZEN=false
C1_EXECUTION_AUTHORIZATION_ISSUED=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=merge-post-merge-verify-then-C1-request-freeze-and-authorization
```

## `C1`: train-only dataset isolation correction authored (ADR-126)

C1 request-freeze admission remained closed because the scientific live-data
path delegated dataset preflight to torchvision before train-only materialization.
ADR-126 makes the invariant project-owned: the request schema can bind only the
two canonical uncompressed train IDX files, and the scientific runtime parses
only those files without a torchvision Dataset constructor. The current frozen
image remains immutable but is not C1-admissible; no C1 authorization is consumed.

```text
C1_TRAIN_ONLY_DATASET_ISOLATION_CORRECTION_AUTHORED=true
RUNTIME_SOURCE_MANIFEST_SHA256=sha256:01d86f045bf42554382654d2c48f2be23f4763b6fbdc4aa1c9e7cff939367561
CURRENT_SUPERSEDING_IMAGE_C1_ADMISSIBLE=false
NEW_SCIENTIFIC_IMAGE_REQUIRED=true
NEW_SCIENTIFIC_IMAGE_BUILT=false
C1_REQUEST_FREEZE_AUTHORIZATION_CONSUMED=false
C1_REQUEST_FROZEN=false
C1_EXECUTION_AUTHORIZATION_ISSUED=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=merge-post-merge-verify-then-corrected-image-build-validation-freeze
```


## `C1`: corrected scientific image frozen and being repository-integrated (ADR-127)

After ADR-126, the corrected scientific runtime was merged as `3858d3a7e6d7b3401e999523bc6675dc7dd0223d` and
built exactly once into new image `sha256:89703b0b37b2729855835a6ed19ba1ca397ae14614c318344bd7625d12c727ef`. The image passed
the 157-path runtime closure check, a dedicated `5 passed` train-only isolation
validation, the `45 passed` targeted validation, was frozen, and was
independently verified without a rebuild.

ADR-127 integrates the original evidence byte-for-byte and binds it to the
repository. Previous image `sha256:7aefbc241ad725f4ac31d8b72c63a82247516ad4831aad6f7d0ef89817f9dacb` remains preserved as the
historical superseding image but stays C1-inadmissible. The previously issued
C1 request-freeze authorization is not consumed.

```text
CORRECTED_SCIENTIFIC_IMAGE_DIGEST=sha256:89703b0b37b2729855835a6ed19ba1ca397ae14614c318344bd7625d12c727ef
CORRECTED_SCIENTIFIC_IMAGE_FREEZE_SHA256=sha256:ce8c054c92df18512b2a88ac25148f44c15487d8c2d4e68d8751966ac17bf287
CORRECTED_SCIENTIFIC_IMAGE_FREEZE_INDEPENDENTLY_VERIFIED=true
TRAIN_ONLY_ISOLATION_VALIDATED=true
RUNTIME_SOURCE_MANIFEST_SHA256=sha256:01d86f045bf42554382654d2c48f2be23f4763b6fbdc4aa1c9e7cff939367561
REPOSITORY_INTEGRATION_SHA256=sha256:70012413e1d6bd69dbad060cef0d4b19e0bfe2635eca4dbe746ccfc42544ae72
PREVIOUS_SUPERSEDING_IMAGE_PRESERVED=true
PREVIOUS_SUPERSEDING_IMAGE_C1_ADMISSIBLE=false
C1_REQUEST_FREEZE_AUTHORIZATION_PREVIOUSLY_ISSUED=true
C1_REQUEST_FREEZE_AUTHORIZATION_CONSUMED=false
C1_REQUEST_FREEZE_PERMITTED=false
C1_REQUEST_FROZEN=false
C1_EXECUTION_AUTHORIZATION_ISSUED=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=merge-post-merge-verify-then-resume-existing-C1-request-freeze-boundary
```

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

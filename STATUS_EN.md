# Research status

[Русская версия](STATUS.md)

As of 22 July 2026, the immutable Stage 1/2, Stage 3A, Stage 3B B0,
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
external seal to the receipt and audit package. The output is now frozen as
repository evidence, while result publication, superiority claims, and `EX-IF0`
remain unauthorized.

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
matched_profiling_analysis_open=false
runtime_authorization=issued_consumed
measurements_allowed=false
results_publication_permitted=false
release_draft_required=true
release_publication_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

These lines restate the existing contract; they do not create a new admission
decision.

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
| Matched-profiling descriptive analysis | single attempt completed; 18 files audited and externally sealed; publication remains closed |
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

After the single analysis attempt, independent audit, and output-sealing PR, the publication boundary remains closed:

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
matched_profiling_analysis_open=false
runtime_authorization=issued_consumed
measurements_allowed=false
results_publication_permitted=false
release_draft_required=true
release_publication_permitted=false
full_stage3b_campaign_complete=false
```

The immutable tag and complete draft `stage3b-matched-profiling-evidence-v1`
release are verified. A separate post-collection/pre-analysis protocol now
freezes estimands, aggregation, the Pareto rule, and `retain / conditional /
reject_or_revise` decisions. The next permitted transition is a separate publication gate for the already
sealed 18-file output. Sealing establishes integrity and provenance but does not
authorize publication or comparative claims. The protocol and draft release do not authorize superiority claims,
`EX-IF0`, `A11-OFF0`, `A11-OFF1`,
the predictor, QWake-PC, or test-split access.

ADR-035 additionally freezes only the post-publication research direction:
oracle search for a minimum sufficient compute aggregate at two scales. This
freeze does not open `EX-IF0` or execution; spike-like dynamics is off the
critical path.

```text
recursive_sufficiency_direction_frozen=true
recursive_aggregate_execution_open=false
global_policy_action=false
spike_like_on_critical_path=false
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
| Verified draft release | `stage3b-matched-profiling-evidence-v1` |

Documentation changes do not regenerate published results.

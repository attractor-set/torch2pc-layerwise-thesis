# Research status

[Русская версия](STATUS.md)

As of 20 July 2026, the immutable Stage 1/2, Stage 3A, Stage 3B B0,
`SI-MA0`, and `SI-MA1` results are published. B1 and B2 preregistration and implementation are complete. Confirmatory B1
is sealed at 120/120 pairs; B2 passed an engineering smoke at 12 triples and
24 comparisons. Confirmatory B2 is preregistered, its fail-closed opening infrastructure is implemented, and its append-only request is frozen, while execution remains closed. The previous shared [matched-profiling](docs/glossary_EN.md#term-matched-profiling) opening artifacts are retained, but production prelaunch blocks them until confirmatory B2.

The full Stage 3B program remains incomplete.

## Machine-checkable current boundary

```text
matched_profiling_manifest_cells=288
scientific_admission=blocked_pending_eq_b2_confirmatory
candidate_aware_runner=complete
b2_confirmatory_opening=implementation_ready_execution_closed
b2_confirmatory_request_frozen=true
matched_profiling_request_refresh_required=true
runtime_authorization=not_issued
measurements_allowed=false
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
| B2 `composite_vjp` | engineering-smoke `EQ-B2=pass`; 12/12 triples and 24/24 comparisons; confirmatory opening infrastructure ready, request frozen, execution closed |
| Matched-profiling request and manifest | previous version retained; production refresh required after confirmatory B2 |
| Matched-profiling runner | candidate-aware implementation complete |
| Matched-profiling execution | not authorized |
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
120/120 pairs. B2 passed an engineering smoke over 12/12 triples and 24/24
comparisons. Smoke `EQ-B2=pass` is not confirmatory admission and does not open
production matched profiling. Admission requires `EQ-B2-CONFIRMATORY`, a
derived `EQ-B2`, and a new versioned request/manifest freeze.

## Current transition

Confirmatory B2 is preregistered as 120 matched triples and 240 direct
comparisons over the same ten validation batches used by confirmatory B1. Its
fail-closed opening infrastructure is implemented with status
`implementation_ready_execution_closed`. The append-only request
`stage3b-b2-confirmatory-120-v1` is frozen for 120 triples and 240 comparisons.
The next incomplete step is immutable-image construction from the publication
commit, lane preflights, separate authorization, and a non-measuring dry-run.

Until positive sealed `EQ-B2-CONFIRMATORY`, derived `EQ-B2` admission, and a
new matched-profiling request/manifest freeze exist:

```text
scientific_admission=blocked_pending_eq_b2_confirmatory
runtime_authorization=not_issued
measurements_allowed=false
```

This documentation update does not authorize B2 execution, the 288-cell
campaign, `EX-IF0`, `A11-OFF0`, `A11-OFF1`, the predictor, QWake-PC, or test
split access.

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

Documentation changes do not regenerate published results.

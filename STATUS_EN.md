# Research status

[Русская версия](STATUS.md)

As of 20 July 2026, the immutable Stage 1/2, Stage 3A, Stage 3B B0,
`SI-MA0`, and `SI-MA1` results are published. B1 and B2 preregistration and implementation are complete. Confirmatory B1 is sealed at 120/120 pairs. Confirmatory B2 is also complete
and sealed: 120/120 triples, 240/240 direct comparisons, all five gates passed,
no failed pairs, and the derived `EQ-B2` admission is preserved. The previous
shared [matched-profiling](docs/glossary_EN.md#term-matched-profiling) opening
artifacts remain historical; production prelaunch requires a new versioned
request/manifest freeze.

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
| B2 `composite_vjp` | `EQ-B2-CONFIRMATORY=pass`; 120/120 triples, 240/240 comparisons, 0 failed pairs; derived `EQ-B2` preserved |
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
120/120 pairs. B2 passed an engineering smoke and then the confirmatory campaign over
120/120 triples and 240/240 direct comparisons. `EQ-B2-CONFIRMATORY=pass` is
sealed, and the derived `EQ-B2` is linked to it by SHA-256. This completes the
scientific-admission chain, while production matched profiling remains closed
until a new versioned request/manifest freeze and separate runtime
authorization.

## Current transition

The sealed B2 set is published at
`results/stage-3/b2/stage3b-b2-confirmatory-63885e5-v1/`. It contains
`EQ-B2-CONFIRMATORY=pass`, the derived `EQ-B2`, 120 completed append-only
histories, aggregate metrics, and 1,800 structural events. The test split was
not accessed.

The next incomplete step is a new versioned 288-cell matched-profiling
request/manifest freeze that prospectively references the sealed B1 and B2
admissions. The previous request/manifest remains byte-for-byte historical and
is not admitted retrospectively.

Until the new freeze and a separate runtime review exist:

```text
scientific_admission=open
matched_profiling_request_refrozen=true
matched_profiling_request_refresh_required=false
matched_profiling_execution_open=false
runtime_authorization=not_issued
measurements_allowed=false
```

This documentation update and evidence preservation do not authorize the
288-cell campaign, `EX-IF0`, `A11-OFF0`, `A11-OFF1`, the predictor, QWake-PC,
or test-split access.

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

Documentation changes do not regenerate published results.

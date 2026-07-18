# Research status

[Русская версия](STATUS.md)

As of 18 July 2026, the immutable Stage 1/2, Stage 3A, Stage 3B B0,
`SI-MA0`, and `SI-MA1` results are published. B1 and B2 preregistration,
implementation, and equivalence admission are complete. The frozen scientific
admission artifacts for shared [matched profiling](docs/glossary_EN.md#term-matched-profiling) are also complete, and the
candidate-aware runner has been implemented.

The full Stage 3B program remains incomplete.

## Machine-checkable current boundary

```text
matched_profiling_manifest_cells=288
scientific_admission=open
candidate_aware_runner=complete
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
| B1 `isolated_layer_vjp` | implementation complete; `EQ-B1=pass` |
| B2 `composite_vjp` | implementation complete; `EQ-B2=pass` |
| Matched-profiling request and manifest | built and validated; 288 cells |
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

B1 and B2 passed separate CPU `float64` and ROCm `float32` controls.
The sealed `EQ-B1` and `EQ-B2` decisions have `status=pass` and
`failed_pairs=[]`. This opens only scientific admission for shared matched
profiling; it does not establish a runtime or memory benefit.

## Current transition

The frozen B0/B1/B2 matched-profiling request and manifest contain 288 cells.
The candidate-aware runner is implemented and merged into `main`.

The next incomplete step in the existing procedure is the separate
ROCm/float32 runtime freeze. Until a separate admission decision is recorded:

```text
runtime_authorization=not_issued
measurements_allowed=false
```

This documentation update does not authorize execution or open `EX-IF0`,
`A11-OFF0`, `A11-OFF1`, the predictor, hysteresis, active control, or
test-dataset access.

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

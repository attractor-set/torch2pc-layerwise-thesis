# Research status

[Русская версия](STATUS.md)

Stage 1/2 are complete immutable published baselines. The diagnostic and
statistical publication of **Stage 3A** is complete within the validation-only
scope. **Stage 3B B0** canonical execution, validation, sealing, and publication
and its statistical and engineering analysis are also complete and published.
The full Stage 3B program remains incomplete.

| Component | Observed status |
|---|---|
| Validation-only pilot | 96/96; test not evaluated |
| Stage 1 / Stage 2 | 80/80 and 80/80 |
| Stage 2 runtime | `BP ≈ Exact < FixedPred << Strict` |
| Stage 3A same-state probes | 10/10 seeds |
| Stage 3A representation probes | 10/10 seeds |
| Exact–BP numerical controls | 10/10 seeds; 30/30 statistical control rows passed |
| Stage 3A observations | 2250 gradient; 150 representation; 750 cross-layer CKA |
| Stage 3A confirmatory statistics | 40 gradient + 20 representation comparisons |
| Stage 3A depth analysis | 180 seed-level rows; 24 statistical rows |
| Stage 3A publication figures | 8 PDFs |
| Stage 3B B0 candidate | `stage2_baseline`; `FixedPred` and `Strict` |
| Stage 3B B0 lane | ROCm / float32; synthetic scaling; validation-only |
| Stage 3B B0 execution | 96/96 cells; 96 completed attempts; 0 failed |
| Process isolation | 96 process records; 96 unique child PIDs; fresh child per cell |
| B0 aggregate evidence | 96 cell + 480 region + 48 paired + 32 configuration rows |
| B0 integrity | non-perturbation, completeness, finite-value, and SHA-256 gates passed |
| Stage 3A/B0 test access | the test dataset was not accessed |
| Stage 3B B0 publication | tag/release `stage3b-b0-evidence-v1` |
| B0 analysis statistical unit | `model_seed`; 3 seeds per configuration |
| B0 bounded timing result | median Strict/FixedPred device time `2.327×` |
| B0 bounded memory result | peak allocated `1.328×`; state-inference saved tensors `11.998×` |
| B0 dominant region | `state_inference` for `FixedPred` and `Strict` |
| B0 analysis publication | tag/release `stage3b-b0-analysis-evidence-v1` |
| B0 decision gate | candidate-specific B1/B2 equivalence work: `continue` |
| Full Stage 3B | `full_stage3b_campaign_complete=false` |
| Regression status | current state is reported by CI |

## Published result boundaries

### Stage 3A

The detailed report is published in
[docs/stage3a-statistical-results_EN.md](docs/stage3a-statistical-results_EN.md).
The independently trained model is the statistical unit; layers, batches,
parameters, and samples are repeated observations within a model seed.

Within FashionMNIST, `lenet_classic`, seeds 0–9, and the pinned implementation:

- `FixedPred` nearly preserves gradient direction while strongly attenuating
  the norm in early layers; layer 5 matches the BP targets;
- `Strict` differs from BP in both direction and scale in hidden layers, while
  its output layer remains close to BP;
- `FixedPred` representations are closer to BP than `Strict`;
- gradient norm ratio increases with depth and relative L2 decreases;
- CKA has no reliable monotonic depth trend, while RSA has a moderate positive
  trend.

### Stage 3B B0

The B0 publication establishes completeness, provenance, and integrity for the
canonical `stage2_baseline` profiling baseline. The published B0 analysis adds
bounded comparative findings about time, memory, region attribution, and
scaling without increasing the independent `n` beyond three model seeds per
configuration.

Recorded provenance:

- execution source `95c25d35224abd5e741f1df9327662ff2fde23ad`;
- sealing source `caa226cc1cd5d4aa0f9772c1fb997f7388d60730`;
- publication state `ed0d48063a17e2d9c6679869a4d930f933877052`;
- archive inventory
  `9abc6434b0f59b510e14ef0ad09d5c3b92a4a9472a90974cb92cdb1657e232ed`;
- seal digest
  `6a3d61838810e559a39f13e6ac39d6b22624c21d72523bddb55c33e83063c93e`;
- analysis implementation `e7a1632a947fae578e877826f0c923342669430e`;
- analysis publication state `b9ff8b2ab76f8752b15dd3bb968565d05f1fe9d3`;
- analysis publication tag `stage3b-b0-analysis-evidence-v1`.


Published bounded observations:

- median Strict/FixedPred device-time ratio: `2.327×`
  (configuration range `1.966–2.619×`);
- median Strict/FixedPred peak-allocated ratio: `1.328×`;
- `state_inference` is the dominant device-time region for both methods;
- median Strict/FixedPred saved-tensor ratio in `state_inference`: `11.998×`.

This is descriptive engineering analysis for the pinned ROCm/float32 synthetic
matrix. It is not a universal method ranking and does not support structural
locality claims without additional measurements.

## Publication artifacts

- Stage 3A [statistics](results/stage3/layerwise/confirmatory/statistics/) and
  [figures](results/stage3/layerwise/confirmatory/figures/);
- Stage 3B B0
  [sealed evidence](results/stage-3/profiling/b0/sealed-v1/);
- Stage 3B B0
  [engineering analysis](results/stage-3/profiling/b0/analysis-v1/);
- GitHub Releases
  [`stage3b-b0-evidence-v1`](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage3b-b0-evidence-v1)
  and
  [`stage3b-b0-analysis-evidence-v1`](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage3b-b0-analysis-evidence-v1).

Committed evidence is not regenerated by this documentation synchronization.

## Next step

Proceed to **Stage 3B B1/B2 candidate-specific numerical equivalence gates**:

- formalize B1 and B2 candidates relative to the published B0 baseline;
- implement each candidate separately;
- evaluate registered cosine, relative-L2, finite-value, and stability gates;
- keep test access disabled;
- run a small profiling pilot only for candidates that pass numerical
  equivalence gates;
- authorize the full matched B1/B2 profiling matrix only through a separate
  decision gate.

Structural locality claims remain blocked until dedicated measurements cover
dependency radius, graph span/lifetime, feedback operator, and orchestration
barriers.

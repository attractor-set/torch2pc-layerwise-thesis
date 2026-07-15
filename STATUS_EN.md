# Research status

[Русская версия](STATUS.md)

Stage 1 and Stage 2 are complete immutable published baselines. Stage 3A
diagnostics and statistical publication are complete within the
validation-only scope. Stage 3B B0 canonical execution, validation, integrity
sealing, evidence publication, and statistical and engineering analysis are
complete. The full Stage 3B program remains incomplete.

## Status summary

| Component | Verified state |
|---|---|
| Validation-only pilot | 96/96; the test dataset was not accessed |
| Stage 1 / Stage 2 | 80/80 and 80/80 |
| Stage 2 runtime | `BP ≈ Exact < FixedPred << Strict` |
| Stage 3A same-state gradient probes | 10/10 seeds |
| Stage 3A representation probes | 10/10 seeds |
| Exact–BP numerical controls | 10/10 seeds; 30/30 statistical control rows passed |
| Stage 3A observations | 2250 gradient; 150 representation; 750 cross-layer CKA |
| Stage 3A confirmatory statistics | 40 gradient and 20 representation comparisons |
| Stage 3A depth analysis | 180 seed-level rows; 24 statistical rows |
| Stage 3A publication figures | 8 PDF files |
| Stage 3B B0 candidate | `stage2_baseline`; `FixedPred` and `Strict` |
| Stage 3B B0 scope | ROCm/float32; synthetic scaling; validation-only |
| Stage 3B B0 execution | 96/96 cells; 96 completed attempts; 0 failed |
| Process isolation | 96 records; 96 unique child PIDs; fresh process per cell |
| B0 aggregate evidence | 96 cell, 480 region, 48 paired, and 32 configuration rows |
| B0 integrity | non-perturbation, completeness, finite-value, and SHA-256 checks passed |
| Stage 3A/B0 test access | the test dataset was not accessed |
| B0 publication | tag and Release `stage3b-b0-evidence-v1` |
| B0 independent unit | independently trained model identified by `model_seed`; 3 per configuration |
| B0 bounded timing result | median Strict/FixedPred device-time ratio `2.327×` |
| B0 bounded memory result | peak allocated memory `1.328×`; state-inference saved tensors `11.998×` |
| B0 dominant region | `state_inference` for both methods |
| B0 analysis publication | tag and Release `stage3b-b0-analysis-evidence-v1` |
| Post-B0 decision | continue candidate-specific B1/B2 equivalence testing |
| Full Stage 3B | `full_stage3b_campaign_complete=false` |
| Regression checks | CI reports the current state |

## Published result boundaries

### Stage 3A

The detailed report is published in
[docs/stage3a-statistical-results_EN.md](docs/stage3a-statistical-results_EN.md).
The independently trained model is the statistical unit. Layers, batches,
parameters, and samples are repeated observations within one `model_seed`.

Within FashionMNIST, `lenet_classic`, seeds 0–9, and the pinned implementation:

- `FixedPred` nearly preserves gradient direction while strongly attenuating
  the norm in early layers; layer 5 approaches the BP target;
- `Strict` differs from BP in direction and scale in hidden layers, while the
  output layer remains close to BP;
- `FixedPred` representations are closer to BP than `Strict` representations;
- gradient-norm ratio increases with depth and relative L2 decreases;
- CKA has no reliable monotonic depth trend, whereas RSA has a moderate
  positive trend.

These observations do not automatically generalize to other architectures,
datasets, implementations, or compute environments.

### Stage 3B B0

The B0 publication establishes completeness, provenance, and integrity for the
canonical `stage2_baseline` profiling baseline. The published analysis adds
bounded comparisons of time, memory, measured-region attribution, and scaling.
The number of independent units remains three models per configuration.

Recorded provenance:

- execution source `95c25d35224abd5e741f1df9327662ff2fde23ad`;
- integrity-sealing source `caa226cc1cd5d4aa0f9772c1fb997f7388d60730`;
- publication state `ed0d48063a17e2d9c6679869a4d930f933877052`;
- archive inventory checksum
  `9abc6434b0f59b510e14ef0ad09d5c3b92a4a9472a90974cb92cdb1657e232ed`;
- sealed-bundle digest
  `6a3d61838810e559a39f13e6ac39d6b22624c21d72523bddb55c33e83063c93e`;
- analysis implementation `e7a1632a947fae578e877826f0c923342669430e`;
- analysis publication state
  `b9ff8b2ab76f8752b15dd3bb968565d05f1fe9d3`;
- analysis publication tag `stage3b-b0-analysis-evidence-v1`.

Published bounded findings:

- median Strict/FixedPred device-time ratio: `2.327×`, with a configuration
  range of `1.966–2.619×`;
- median Strict/FixedPred peak-allocated-memory ratio: `1.328×`;
- `state_inference` is the dominant device-time region for `FixedPred` and
  `Strict`;
- median Strict/FixedPred saved-tensor ratio within `state_inference`: `11.998×`.

This is descriptive engineering analysis of the pinned ROCm/float32 synthetic
matrix. It is not a universal method ranking and does not establish structural
locality without dedicated measurements.

## Publication artifacts

- Stage 3A [statistics](results/stage3/layerwise/confirmatory/statistics/) and
  [figures](results/stage3/layerwise/confirmatory/figures/);
- Stage 3B B0 [sealed evidence](results/stage-3/profiling/b0/sealed-v1/);
- Stage 3B B0 [engineering analysis](results/stage-3/profiling/b0/analysis-v1/);
- GitHub Releases
  [`stage3b-b0-evidence-v1`](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage3b-b0-evidence-v1)
  and
  [`stage3b-b0-analysis-evidence-v1`](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage3b-b0-analysis-evidence-v1).

Published evidence is not regenerated by documentation changes.

## Next stage

The next factual stage is Scenario A validity control:

- shortcut/equivalence controls with instrumentation disabled;
- observer non-interference and observer overhead;
- deterministic NCZ/ECZ/TNZ controls;
- after they pass, SI-MA0 and candidate-specific B1/B2 gates.

Full matched profiling, active QWake-PC, and test access remain blocked pending
their own authorization decisions.

## Accepted post-B0 design decision

Scenario A is adopted as the primary Stage 3B working plan. The decision is
recorded in [ADR-012](docs/decisions/ADR-012-pc-tref-pc-catm-scenario-a_EN.md),
the upper-level framework in [PC-TREF Balanced Core](docs/pc-tref-balanced-core_EN.md), the mechanism model in [PC-CATM](docs/pc-catm-operator-model_EN.md), and the
sequence in the [Scenario A plan](docs/stage3b-primary-scenario-a_EN.md). This is
a design freeze, not completed experimental execution. This freeze completes
only A0; the next factual stage is shortcut and observer controls. B0 and test
access remain unchanged.

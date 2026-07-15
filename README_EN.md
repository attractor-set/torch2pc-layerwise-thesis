# Torch2PC Layer-wise Thesis

[Русская версия](README.md)

A master's thesis research repository for comparing backpropagation and
Torch2PC predictive-coding regimes. The repository separates assumptions,
observations, procedures, and interpretations.

## Research stance

The project adopts a neutral observer position:

- no method is assumed to be superior in advance;
- theoretical expectations are treated as testable assumptions;
- failure to detect a difference is not treated as equivalence without a
  dedicated equivalence analysis;
- empirical statements are accepted only within a pre-specified experiment and
  a recorded environment;
- negative, mixed, and unstable outcomes are retained;
- conclusions remain limited to the studied implementation, architectures,
  datasets, and compute environment.

## Research question

Under which algorithmic and computational conditions do `Exact`, `FixedPred`,
and `Strict` produce observations close to backpropagation, and when do the
observed differences exceed pre-specified numerical or statistical bounds?

## Observed status on 15 July 2026

The following baseline and diagnostic campaigns are complete in the pinned
Ubuntu/ROCm environment:

- validation-only pilot: **96/96** terminal cells, 0 failed, no test evaluation;
- Stage 1: **80/80**, original Torch2PC
  `00c6c50ee3540537bbb56ab2b6567b541f42b093`;
- Stage 2: **80/80**, patched Torch2PC
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- Stage 3A: layer-wise diagnostics, seed-level statistics, depth analysis, and
  publication figures are published;
- Stage 3B B0: the ROCm/float32 canonical baseline completed **96/96**, with no
  failed attempts or systemic resource failures; every cell ran in a fresh
  Python child process;
- the Stage 3B B0 statistical and engineering analysis is published as
  deterministic derived evidence with `model_seed` as the independent unit and
  three seeds per configuration;
- neither Stage 3A nor Stage 3B B0 accessed the test dataset.

CI is the source of truth for the current regression-suite status; the
repository documentation does not pin a quickly stale passing-test count.

Relative to Stage 1 mean total training time, Exact was approximately 14%
faster, FixedPred 31% faster, and Strict 26% faster; BP was effectively
unchanged. Complete paired records are available in
[`results/cross-version/`](results/cross-version/).

### Execution and publication states

| Role | Identifier |
|---|---|
| Stage 1 source lock | `140e77cc2083bf04234dcea16b95803e63cb0537` |
| Stage 2 execution source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Stage 2 results/publication state | `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| Stage 3A publication tag | `stage3a-statistical-publication-v1` |
| Stage 3B B0 execution source | `95c25d35224abd5e741f1df9327662ff2fde23ad` |
| Stage 3B B0 sealing source | `caa226cc1cd5d4aa0f9772c1fb997f7388d60730` |
| Stage 3B B0 publication state | `ed0d48063a17e2d9c6679869a4d930f933877052` |
| Stage 3B B0 publication tag | `stage3b-b0-evidence-v1` |
| Stage 3B B0 analysis implementation | `e7a1632a947fae578e877826f0c923342669430e` |
| Stage 3B B0 analysis publication state | `b9ff8b2ab76f8752b15dd3bb968565d05f1fe9d3` |
| Stage 3B B0 analysis publication tag | `stage3b-b0-analysis-evidence-v1` |

The
[`stage2-results-v1` GitHub Release](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage2-results-v1)
contains the Stage 2 replication bundle. The
[`stage3b-b0-evidence-v1` GitHub Release](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage3b-b0-evidence-v1)
pins the compact Stage 3B B0 derived-evidence bundle, its provenance, and its
checksums. The
[`stage3b-b0-analysis-evidence-v1` GitHub Release](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage3b-b0-analysis-evidence-v1)
publishes the deterministic statistical and engineering analysis of that
baseline.

Stage 1, Stage 2, Stage 3A, the Stage 3B B0 measurement baseline, and its B0
analysis are complete within their registered scopes and are not intended to be
rerun. The full Stage 3B program remains incomplete.

See [RESEARCH_PRINCIPLES_EN.md](RESEARCH_PRINCIPLES_EN.md) and
[STATUS_EN.md](STATUS_EN.md).

## Stage 3A: diagnostics and statistical publication complete

The validation-only confirmatory subcampaign covers FashionMNIST,
`lenet_classic`, and seeds 0–9. Same-state gradient probes and independently
trained representation comparisons are complete for every seed; all 10
Exact–BP controls passed. Published outputs include:

- 2250 gradient observations;
- 150 corresponding CKA/RSA observations;
- 750 cross-layer CKA observations;
- 40 gradient and 20 representation confirmatory comparisons;
- 24 depth-analysis rows;
- 8 publication PDF figures;
- metadata and SHA-256 manifests for statistics and figures.

The bounded primary finding is that, within the studied configuration,
`FixedPred` nearly preserves gradient direction while strongly attenuating the
norm in early layers; magnitude approaches BP toward the output. `Strict`
differs from BP in both direction and magnitude in hidden layers. `FixedPred`
representations remain closer to BP than `Strict`. Gradient norm ratio
increases with depth and relative L2 decreases; CKA has no reliable monotonic
trend, while RSA has a moderate positive trend.

Detailed bilingual report:
[docs/stage3a-statistical-results_EN.md](docs/stage3a-statistical-results_EN.md).

Publication artifacts:

- [statistics](results/stage3/layerwise/confirmatory/statistics/), including
  `analysis_metadata.json`, `depth_analysis_metadata.json`, and `SHA256SUMS`;
- [figures](results/stage3/layerwise/confirmatory/figures/), including
  `figure_metadata.json` and `SHA256SUMS`.

Conclusions are limited to FashionMNIST, `lenet_classic`, seeds 0–9, the pinned
implementation, and the validation-only Stage 3A protocol.

## Stage 3B B0: baseline, evidence, and engineering analysis published

B0 fixes the `stage2_baseline` candidate for `FixedPred` and `Strict` in an
ROCm/float32 synthetic scaling campaign. The canonical protocol used 20 warm-up
steps, 5 repetitions, and 50 measured steps. Completed outputs include:

- 96/96 canonical cells and 96/96 completed attempts;
- 0 failed attempts and 0 systemic resource failures;
- 96 process records and 96 unique child PIDs;
- 48 `FixedPred` and 48 `Strict` cells;
- 96 cell-level, 480 region-level, 48 paired-method, and 32 configuration rows;
- five measured regions: `initial_forward`, `state_inference`,
  `local_state_vjp`, `parameter_vjp`, and `optimizer_step`;
- non-perturbation, completeness, and finite-value gates.

The compact evidence bundle is published under
[`results/stage-3/profiling/b0/sealed-v1/`](results/stage-3/profiling/b0/sealed-v1/).
Seal digest:
`6a3d61838810e559a39f13e6ac39d6b22624c21d72523bddb55c33e83063c93e`.

The claim boundary is explicit:

- `evidence=true`;
- `full_b0_campaign_complete=true`;
- `results_publication_permitted=true`;
- `full_stage3b_campaign_complete=false`;
- `test_dataset_access=false`.

The deterministic analysis is published under
[`results/stage-3/profiling/b0/analysis-v1/`](results/stage-3/profiling/b0/analysis-v1/).
The independent statistical unit is `model_seed`, with three seeds per
configuration, so the findings are bounded to descriptive engineering analysis.

Published bounded observations for the synthetic ROCm/float32 matrix include:

- median Strict/FixedPred device-time ratio: **2.327×**
  (configuration range 1.966–2.619×);
- median peak-allocated ratio: **1.328×**;
- dominant device-time region for both methods: `state_inference`;
- median Strict/FixedPred saved-tensor ratio in `state_inference`: **11.998×**.

The decision gate permits candidate-specific B1/B2 numerical-equivalence work.
Full matched B1/B2 profiling remains blocked until those gates pass, while
structural locality claims remain blocked until dependency-radius,
graph-span/lifetime, feedback-operator, and orchestration-barrier measurements
are available. A new B0 execution is not required.

## Pilot evidence export

`make pilot` generates both `pilot_selection.json` and the compact, verified
`pilot_observations.csv`. The latter can be regenerated while the original run
directories and pilot environment lock are still available:

```bash
make select-pilot
make pilot-observations
```

## Reproduction from scratch

The following sequence is for independent reproduction, not for repeating the
completed Stage 1/2 campaigns.

```bash
cp .env.example .env
./scripts/setup_ubuntu.sh
make init
make host-check
make image-check
make pin-base-image
make build
make validate
make prepare
```

`make pin-base-image` replaces the mutable Docker tag in the local `.env` with
an immutable `repository@sha256:...` reference. Pilot and final images are built
only after this step. The local `.env` is not committed.

See [docs/validation_EN.md](docs/validation_EN.md) for the validation procedure.


## Public and local artifacts

Downloaded papers, datasets, private notes, and heavyweight checkpoints are not
stored in Git. Code, protocols, configurations, aggregate results, and
manifests are versioned. The complete Stage 2 raw artifacts are distributed in
the `stage2-results-v1` replication bundle.

## Licensing

- software code is distributed under the Apache License 2.0 — see
  [LICENSE](LICENSE);
- original thesis, article, documentation, table, and figure content is
  distributed under the Creative Commons Attribution 4.0 International license
  — see [LICENSE-DOCS](LICENSE-DOCS) and
  [LICENSE-DOCS_EN](LICENSE-DOCS_EN);
- third-party materials retain their original licenses and attribution terms —
  see [NOTICE](NOTICE) and [NOTICE_EN](NOTICE_EN).

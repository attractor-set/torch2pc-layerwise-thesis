# Research status

[Русская версия](STATUS.md)

Stage 1/2 are complete immutable published baselines. The diagnostic and
statistical publication of **Stage 3A** is complete within the validation-only
scope. Locality, profiling, exact execution, and acceleration remain separate
future subcampaigns.

| Component | Observed status |
|---|---|
| Validation-only pilot | 96/96; test not evaluated |
| Stage 1 / Stage 2 | 80/80 and 80/80 |
| Stage 2 runtime | `BP ≈ Exact < FixedPred << Strict` |
| Stage 3A same-state probes | 10/10 seeds |
| Stage 3A representation probes | 10/10 seeds |
| Exact–BP numerical controls | 10/10 seeds; 30/30 statistical control rows passed |
| Gradient observations | 2250; cosine defined for 2250/2250 |
| Representation observations | 150; RSA defined for 150/150 |
| Cross-layer CKA observations | 750 |
| Confirmatory statistics | 40 gradient + 20 representation comparisons |
| Depth analysis | 180 seed-level rows; 24 statistical rows |
| Publication figures | 8 PDF |
| Regression suite | 120 passed |
| Evidence integrity | statistics and figures SHA256SUMS present |
| Stage 3A test access | validation-only diagnostics; no test loader created |
| Broader Stage 3 | requires separate preregistrations, gates, and provenance chains |

## Current interpretation

The detailed report is published in
[docs/stage3a-statistical-results_EN.md](docs/stage3a-statistical-results_EN.md).
The independently trained model is the statistical unit; layers, batches,
parameters, and samples are repeated observations within a model seed.

Within FashionMNIST, `lenet_classic`, seeds 0–9, and the pinned implementation:

- `FixedPred` nearly preserves gradient direction while strongly attenuating
  the norm in early layers; layer 5 matches the BP targets;
- `Strict` differs from BP in both direction and scale in hidden layers, while
  its output layer remains close to BP;
- `FixedPred` representations are closer to BP than `Strict`, although both
  groups differ from the ideal BP target in CKA/RSA;
- gradient norm ratio increases with depth and relative L2 decreases;
- CKA has no reliable monotonic depth trend, while RSA has a moderate positive
  trend.

## Publication artifacts

- [statistics](results/stage3/layerwise/confirmatory/statistics/): tables,
  `analysis_metadata.json`, `depth_analysis_metadata.json`, and `SHA256SUMS`;
- [figures](results/stage3/layerwise/confirmatory/figures/): 8 PDFs,
  `figure_metadata.json`, and `SHA256SUMS`.

Committed evidence is not regenerated during the documentation-only Stage 3A
closure.

## Next step

After the Stage 3A publication merge, the next stage starts from updated
`main` in a separate `stage3b-profiling-locality-preregistration` branch. The
first commit should freeze a profiling/locality preregistration with
validation-only access, model seed as the independent unit, warm-up and
synchronization rules, timing and memory attribution, locality taxonomy,
failure/exclusion criteria, and no acceleration claims before measurement
gates pass.

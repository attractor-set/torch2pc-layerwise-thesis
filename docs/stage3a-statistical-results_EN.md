# Stage 3A: statistical results of the layer-wise diagnostics

[Русская версия](stage3a-statistical-results.md)

## Scope

Stage 3A is a confirmatory diagnostic subcampaign executed in the pinned
Ubuntu/ROCm environment within one experimental scope:

- dataset: FashionMNIST;
- architecture: `lenet_classic`;
- methods: BP, `Exact`, `FixedPred`, and `Strict`;
- model seeds: 0–9;
- data access: validation-only diagnostic probes;
- statistical unit: the independently trained model seed.

Layers, batches, parameters, and samples are repeated observations within a
seed and do not increase the number of independent replications. Stage 3A does
not create a test loader and does not modify the completed Stage 1/2 execution
or publication states.

The frozen analysis plan is available at
[`experiments/planned/STAGE3A-STATISTICAL-ANALYSIS.md`](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/stage3a-statistical-publication-v1/experiments/planned/STAGE3A-STATISTICAL-ANALYSIS.md).

## Inputs and published outputs

| Artifact | Size |
|---|---:|
| Gradient observations | 2250 |
| Corresponding CKA/RSA observations | 150 |
| Cross-layer CKA observations | 750 |
| Seed-level gradient rows | 600 |
| Seed-level representation rows | 300 |
| Gradient statistical comparisons | 40 |
| Representation statistical comparisons | 20 |
| Exact numerical control rows | 30 |
| Depth seed-level rows | 180 |
| Depth statistical rows | 24 |
| Publication figures | 8 PDF |

All registered statistical comparisons have `n=10` and `n_missing=0`.

## Statistical protocol

Seed-level aggregates were constructed first. Paired comparisons were then
performed against the pre-specified BP targets:

- cosine, norm ratio, and sign agreement: target `1`;
- relative L2: target `0`;
- CKA and RSA Spearman: target `1`;
- depth Spearman: no monotonic trend target `0`.

The analysis uses exact two-sided sign-flip tests, within-family Holm
correction, intervals for the mean paired difference, `Cohen dz`, and
rank-biserial correlation. Linear depth slopes are retained as descriptive
estimates; confirmatory depth inference uses seed-level Spearman coefficients.

## Exact numerical control

All 30 main Exact control rows passed the registered tolerance of `1e-12`.
The largest observed absolute error was `1.354472090042691e-14`.

The depth control also retained a practically zero Exact trend:

- maximum value range: `1.354472090042691e-14`;
- maximum absolute slope: `1.1546319456101628e-15`.

These controls support the consistency of extraction, aggregation, and pairing
within the pinned scope. They are not a universal proof of algorithmic
equivalence between Torch2PC and BP.

## FixedPred gradients

At layers 0, 1, 3, and 4, all four registered metrics differ from the BP
targets after Holm correction (`p_holm=0.0390625`). At output layer 5, the
values match the targets within numerical precision and `p_holm=1`.

| Layer | Cosine | Norm ratio | Relative L2 | Sign agreement |
|---:|---:|---:|---:|---:|
| 0 | 0.994574 | 0.000881 | 0.999123 | 0.956667 |
| 1 | 0.999932 | 0.008326 | 0.991675 | 0.996358 |
| 3 | 1.000000 | 0.225160 | 0.774840 | 0.999793 |
| 4 | 1.000000 | 0.612580 | 0.387420 | 0.999848 |
| 5 | 1.000000 | 1.000000 | 0.000000 | 1.000000 |

Within the studied configuration, `FixedPred` nearly preserves gradient
direction while strongly suppressing the norm in early layers. The scale
approaches BP toward the output, and layer 5 matches the BP targets.

## Strict gradients

All 20 layer/metric comparisons for `Strict` differ from the BP targets after
Holm correction (`p_holm=0.0390625`). Hidden layers show both direction and
scale mismatch:

- cosine: approximately `0.843–0.927`;
- sign agreement: approximately `0.822–0.868`;
- norm ratio increases from `0.000584` at layer 0 to `0.311747` at layer 4;
- relative L2 decreases from `0.999471` to `0.720317` across hidden layers.

Output layer 5 is close to BP but not identical:

- cosine: `0.9999987`;
- norm ratio: `0.998449`;
- relative L2: `0.002240`;
- sign agreement: `0.999482`.

In this scope, `Strict` produces both depth-dependent scaling and a visible
direction mismatch in hidden layers.

## Neural representations

All 20 CKA/RSA comparisons differ from the ideal BP target `1` after Holm
correction (`p_holm=0.01953125`). `FixedPred` remains systematically closer to
BP than `Strict`:

| Method | CKA range | RSA range |
|---|---:|---:|
| FixedPred | 0.988599–0.993861 | 0.983237–0.993475 |
| Strict | 0.960907–0.978650 | 0.940177–0.971826 |

A statistical difference from the ideal target does not automatically imply a
large practical effect. The absolute CKA/RSA deviations for `FixedPred` remain
small within the studied configuration.

## Depth analysis

Confirmatory depth inference uses one Spearman coefficient per seed over
ordinal layer depth.

| Domain | Method | Metric | Mean rho | Holm p |
|---|---|---|---:|---:|
| gradient | FixedPred | cosine | 1.00 | 0.0078125 |
| gradient | FixedPred | norm ratio | 1.00 | 0.0078125 |
| gradient | FixedPred | relative L2 | -1.00 | 0.0078125 |
| gradient | FixedPred | sign agreement | 0.97 | 0.0078125 |
| gradient | Strict | cosine | 0.54 | 0.0078125 |
| gradient | Strict | norm ratio | 1.00 | 0.0078125 |
| gradient | Strict | relative L2 | -1.00 | 0.0078125 |
| gradient | Strict | sign agreement | 0.59 | 0.0078125 |
| representation | FixedPred | CKA | -0.01 | 1.0000000 |
| representation | FixedPred | RSA | 0.47 | 0.0351563 |
| representation | Strict | CKA | -0.19 | 0.3027344 |
| representation | Strict | RSA | 0.51 | 0.0312500 |

Gradient norm ratio increases with depth and relative L2 decreases for both
predictive-coding regimes. CKA has no reliable monotonic depth trend. RSA has a
moderate positive trend for both `FixedPred` and `Strict`.

## Cross-layer CKA

Cross-layer CKA is retained as a descriptive evidence set with 750
observations. The candidate-method matrices have their largest mean values on
matched layers:

| Method | Mean matched-layer CKA | Mean off-diagonal CKA |
|---|---:|---:|
| FixedPred | 0.991851 | 0.857415 |
| Strict | 0.972458 | 0.848253 |

The matrices visualize the structure of inter-layer similarity, but they do
not form a separate registered confirmatory inferential family. Cross-layer
results are therefore interpreted descriptively.

## Effect-size and p-value caveats

- Exact sign-flip p-values are discrete at `n=10`; the minimum two-sided value
  is `0.001953125`.
- Very large absolute `Cohen dz` values for norm ratio and relative L2 arise
  under near-zero between-seed variance. They indicate a stable deviation from
  the target, not a universal measure of practical importance.
- Significance against ideal `1/0` targets does not replace evaluation of
  training quality, runtime, memory, or downstream utility.
- Layers and batches are not independent replications.

## Threats to validity

1. One dataset and one architecture were studied.
2. The analysis contains 10 independently trained seeds.
3. The campaign is limited to validation-only diagnostic probes.
4. Results apply to the pinned Torch2PC commits, dtype, configurations, and
   Ubuntu/ROCm environment.
5. Representation comparisons use independently trained checkpoints, so the
   conclusion is bounded by the registered CKA/RSA procedures.
6. New datasets, architectures, hyperparameters, hardware, or implementations
   require a separate preregistered campaign.

## Bounded conclusions

Within the studied configuration:

- `Exact` passes the registered numerical controls against BP;
- `FixedPred` primarily preserves gradient direction while producing strong
  early-layer magnitude attenuation;
- `Strict` differs from BP in both direction and magnitude in hidden layers;
- `FixedPred` representations are closer to BP than `Strict`, although both
  groups differ statistically from the ideal BP target;
- gradient alignment has a pronounced depth-dependent structure;
- CKA has no reliable monotonic depth trend, while RSA has a moderate positive
  trend.

These conclusions do not extend beyond FashionMNIST, `lenet_classic`, seeds
0–9, the pinned implementation, and the validation-only Stage 3A protocol.

## Artifacts and provenance

Statistics:

- [statistics directory](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/stage3a-statistical-publication-v1/results/stage3/layerwise/confirmatory/statistics);
- [analysis metadata](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/stage3a-statistical-publication-v1/results/stage3/layerwise/confirmatory/statistics/analysis_metadata.json);
- [depth analysis metadata](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/stage3a-statistical-publication-v1/results/stage3/layerwise/confirmatory/statistics/depth_analysis_metadata.json);
- [statistics SHA256SUMS](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/stage3a-statistical-publication-v1/results/stage3/layerwise/confirmatory/statistics/SHA256SUMS).

Figures:

- [figures directory](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/stage3a-statistical-publication-v1/results/stage3/layerwise/confirmatory/figures);
- [figure metadata](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/stage3a-statistical-publication-v1/results/stage3/layerwise/confirmatory/figures/figure_metadata.json);
- [figures SHA256SUMS](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/stage3a-statistical-publication-v1/results/stage3/layerwise/confirmatory/figures/SHA256SUMS).

Committed evidence is verified without regeneration:

```bash
(
  cd results/stage3/layerwise/confirmatory/statistics
  sha256sum -c SHA256SUMS
)

(
  cd results/stage3/layerwise/confirmatory/figures
  sha256sum -c SHA256SUMS
)
```

# Analysis plan

[Русская версия](analysis-plan.md)

## Primary analysis

FashionMNIST is the primary [dataset](glossary_EN.md#term-dataset), macro-F1 is the primary metric, and an
independently trained model is the [independent statistical unit](glossary_EN.md#term-statistical-unit). The primary
paired comparisons are FixedPred versus BP and Strict versus BP. Each
comparison requires at least ten complete pairs with matching `model_seed`
values.

For each primary comparison, publish:

- raw values for every independently trained model;
- mean paired difference;
- 95% confidence interval;
- `Cohen dz`;
- an exact paired sign-flip permutation test or the preregistered approximation;
- the Holm-adjusted value;
- a separate equivalence assessment.

## Equivalence

Equivalence is not inferred from the absence of a statistically detectable
difference. It is assessed separately: the 90% confidence interval for the
paired macro-F1 difference must lie entirely inside a prespecified margin. The
working margin of 0.01 is fixed before the [pilot study](glossary_EN.md#term-pilot-study) and is not changed after
pilot or final results are observed.

## Secondary analysis

Secondary outcomes include MNIST, accuracy, loss, training trajectory, Exact,
run success rate, and computational metrics. Secondary analysis is marked
separately and does not replace the primary analysis.

## Layer-wise analysis

Gradient measures are aggregated first within one trained model and then across
models with different `model_seed` values. Individual parameters, layers, and
batches are not treated as independent model replications.

## Representation analysis

Uncertainty for CKA and RSA must include between-model variation. Resampling
images alone is insufficient. The analysis uses hierarchical resampling or
comparisons of model-level estimates.

## Robustness

The same [checkpoint](glossary_EN.md#term-checkpoint) is evaluated on deterministic corruptions with fixed
corruption-generator seeds. Report the clean-data metric, relative degradation,
the slope across severity, and the value at maximum severity.

## Computational cost

Equal-update and equal-wall-clock comparisons are reported separately. The
measurements include [warm-up](glossary_EN.md#term-warm-up), GPU synchronization, deterministic method-order
counterbalancing, repeated measurements, and host-state recording before and
after each series. The post-pilot order and telemetry freeze are documented in
`docs/decisions/ADR-005-post-pilot-final-execution_EN.md`.

## Confirmatory-analysis completeness

A primary contrast is confirmatory only when at least ten complete pairs with
prespecified seed values are available. With fewer pairs, descriptive estimates
are retained, but no Holm-adjusted p-value or equivalence conclusion is formed.

The pilot [configuration](glossary_EN.md#term-configuration) is selected using FashionMNIST validation data only. MNIST is
a secondary transfer assessment and does not participate in [candidate](glossary_EN.md#term-candidate) ranking.

## Stage 3 addendum

Stage 3 does not modify the Stage 1/2 [confirmatory analysis](glossary_EN.md#term-confirmatory-analysis). It uses separate
analysis units:

- training quality: an independently trained model;
- [profiling](glossary_EN.md#term-profiling): a matched [experiment cell](glossary_EN.md#term-experiment-cell) or repetition within a hardware block;
- locality: events aggregated within a run before analysis across trained models;
- gradient alignment: layers aggregated within a model before between-model
  analysis.

B1 and B2 use numerical-equivalence checks and paired [runtime](glossary_EN.md#term-runtime)/memory
observations. C1 and C2 use validation [non-inferiority](glossary_EN.md#term-non-inferiority), gradient alignment, and
compute reduction. The final [non-inferiority](glossary_EN.md#term-non-inferiority) margin is fixed before Stage 3
test access. See the [Stage 3 protocol](stage-3-protocol_EN.md).

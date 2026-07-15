# Methodology

[Русская версия](methodology.md)

## Design

The study is computational and experimental. Comparisons are paired by
`model_seed`, and an independently trained model is the independent statistical
unit.

## Stages

1. static validation;
2. asset preparation;
3. structural validation of the selected formulas;
4. C0/C1 checks across several model seeds and batches;
5. a validation-only [pilot study](glossary_EN.md#term-pilot-study) without [test-dataset access](glossary_EN.md#term-test-dataset-access);
6. [configuration](glossary_EN.md#term-configuration) freeze;
7. final [execution](glossary_EN.md#term-execution) with test evaluation;
8. layer-wise and computational diagnostics;
9. statistical estimation and interpretation.

## Datasets

- FashionMNIST is the primary [dataset](glossary_EN.md#term-dataset);
- MNIST is the secondary control [dataset](glossary_EN.md#term-dataset);
- KMNIST is a possible extension after the primary analysis.

## Metrics

The primary metric is macro-F1. Secondary metrics are accuracy, loss, run
success rate, [wall-clock time](glossary_EN.md#term-wall-time), peak memory, gradient [cosine similarity](glossary_EN.md#term-cosine-similarity),
[relative L2 error](glossary_EN.md#term-relative-l2-error), CKA, and RSA.

## Configuration selection

The [pilot study](glossary_EN.md#term-pilot-study) uses validation data only. The test [dataset](glossary_EN.md#term-dataset) is not loaded.
FixedPred and Strict configurations are selected with a prespecified metric and
technical tie-breaking rules. A freeze manifest is created after the pilot.

## Final execution

[Final execution](glossary_EN.md#term-final-execution) uses prespecified paired `model_seed` values. The test [dataset](glossary_EN.md#term-dataset) is
evaluated after loading the [checkpoint](glossary_EN.md#term-checkpoint) with the best validation result. Any
[configuration](glossary_EN.md#term-configuration) change after test access belongs to a new [exploratory analysis](glossary_EN.md#term-exploratory-analysis).

## Statistics

Published outputs include raw paired values, the mean difference, a 95%
confidence interval, `Cohen dz`, a paired sign-flip permutation test or the
Wilcoxon signed-rank test, and Holm adjustment. Equivalence is assessed
separately with a 90% confidence interval and a prespecified margin.

## Limitations

Results may depend on the Torch2PC commit, dtype, optimizer, [architecture](glossary_EN.md#term-architecture),
dataset, random-seed policy, and hardware environment. These dependencies are
part of the claim boundary rather than hidden inconveniences.

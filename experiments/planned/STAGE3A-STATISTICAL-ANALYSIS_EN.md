# Stage 3A Statistical Analysis Plan

## 1. Scope

- Dataset: FashionMNIST.
- Architecture: `lenet_classic`.
- Checkpoint: `final`.
- Model seeds: `0–9`.
- Independent statistical unit: independently trained `model_seed`.
- Number of independent observations: `n = 10`.

Individual batches, parameters, and layer pairs are not treated as
independent experimental replications.

## 2. Methods

Primary comparisons:

- FixedPred relative to BP;
- Strict relative to BP.

Exact relative to BP is treated as a numerical implementation control and
is not included in the primary hypothesis families.

## 3. Gradient metrics

The following metrics are analyzed:

- cosine similarity;
- relative L2;
- norm ratio;
- sign agreement.

Raw observations are aggregated within each:

- `model_seed`;
- method;
- layer;
- parameter type;
- metric.

The confirmatory table contains one final value per
`model_seed × method × layer × metric`.

## 4. Representation metrics

The following metrics are analyzed:

- corresponding-layer linear CKA;
- corresponding-layer RSA;
- cross-layer CKA.

Corresponding-layer metrics contain one value per
`model_seed × method × layer × metric`.

Cross-layer CKA describes the layer correspondence structure and is
analyzed separately from corresponding-layer hypotheses.

## 5. Descriptive statistics

For every method, layer, and metric combination, report:

- number of valid seeds;
- mean;
- median;
- standard deviation;
- minimum and maximum;
- 95% confidence interval;
- number of undefined or missing values.

Confidence intervals are calculated at the independent-seed level.

## 6. Hypothesis testing

With `n = 10`, the analysis uses an exact paired sign-flip permutation test.

All `2^10 = 1024` possible sign assignments of the paired differences are
enumerated.

The two-sided p-value is calculated using the absolute observed mean paired
difference.

## 7. Effect sizes

For each paired comparison, report:

- mean paired difference;
- median paired difference;
- standardized paired effect `dz`;
- rank-biserial correlation;
- 95% confidence interval of the mean paired difference.

Interpretation is based on effect magnitude and confidence intervals rather
than p-values alone.

## 8. Multiple-comparison correction

The step-down Holm correction is applied.

Correction is performed separately within the following predefined
families:

1. FixedPred gradient metrics across layers;
2. Strict gradient metrics across layers;
3. FixedPred corresponding-layer CKA/RSA across layers;
4. Strict corresponding-layer CKA/RSA across layers.

The family definitions are frozen before confirmatory outputs are generated.

## 9. Depth analysis

Layer order is mapped to normalized depth `[0, 1]`.

For each `model_seed` and method, calculate the relationship between depth
and the metric using:

- Spearman correlation;
- linear slope as a descriptive quantity.

Statistical inference is performed over the ten seed-level coefficients.
Layers within one network are not treated as independent replications.

## 10. Exact numerical control

For Exact relative to BP, verify:

- cosine similarity close to `1`;
- relative L2 close to `0`;
- norm ratio close to `1`;
- CKA and RSA close to `1`.

Exact is used to detect extraction, aggregation, or matching errors. It is
not used for a substantive superiority hypothesis.

## 11. Undefined-value handling

- Undefined cosine and RSA values remain missing.
- Missing values are not replaced with zero.
- Every output row reports its actual `n`.
- Paired comparisons use only seeds where both paired values are available.
- Any reduction below `n = 10` is explicitly reported.

## 12. Output artifacts

The analysis must generate:

- `seed_level_gradient_metrics.csv`;
- `seed_level_representation_metrics.csv`;
- `gradient_statistics.csv`;
- `representation_statistics.csv`;
- `depth_statistics.csv`;
- `exact_numerical_control.csv`;
- `analysis_metadata.json`;
- figures under the `figures/` directory.

Metadata must record:

- source-code commit;
- SHA-256 hashes of input tables;
- analysis date;
- Python and library versions;
- statistical-family definitions;
- confidence-interval and permutation-test settings.

## 13. Completion criteria

Stage 3A statistical analysis is complete when:

- all ten seeds are included or exclusions are documented;
- Exact passes the numerical control;
- seed-level tables are generated;
- effects, intervals, and exact p-values are calculated;
- Holm correction is applied;
- results are reproducible from the published summary CSV files;
- tests and quality checks pass;
- final tables and figures are committed in a dedicated evidence commit.

## 14. Freeze rule

After this document is committed, the following remain fixed unless a
separate amendment is documented:

- statistical unit;
- aggregation rules;
- primary comparisons;
- metrics;
- correction families;
- hypothesis-testing methods;
- completion criteria.

Any deviation must be recorded as an explicit amendment with a rationale.

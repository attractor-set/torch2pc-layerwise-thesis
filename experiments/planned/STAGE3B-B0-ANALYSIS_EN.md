# Stage 3B B0: statistical and engineering analysis contract

[Русская версия](STAGE3B-B0-ANALYSIS.md)

Status: **analysis implementation authorized; sealed B0 input read-only**.

Freeze date: 2026-07-14.

## 1. Scope

The analysis reads only `results/stage-3/profiling/b0/sealed-v1`. It does not
rerun B0, regenerate committed evidence, or modify the sealed input.

The claim boundary remains:

- `full_b0_campaign_complete=true`;
- `full_stage3b_campaign_complete=false`;
- `test_dataset_access=false`.

## 2. Statistical unit

The independent unit is `model_seed`. Each configuration has seeds `70, 71,
72`, so `n=3`.

Repetitions, measured steps, profiling regions, and cells are nested or
controlled engineering observations. They do not increase the independent
`n`. Because p-values are highly discrete at `n=3`, they are not used for
superiority claims. Primary summaries are median, minimum, maximum, and
directional consistency within matched configurations.

## 3. Registered analyses

1. Paired `Strict` relative to `FixedPred` by
   `depth × width × batch_size × model_seed`.
2. Device/host time and peak allocated/reserved memory.
3. Region attribution across the five registered profiling regions.
4. Region time normalized as a share of the sum of region medians within cell.
5. Seed-level log2 main-effect scaling for depth, width, and batch size.
6. A VJP-region Amdahl upper-bound proxy as an engineering continuation rule.
7. Coverage checks for structural locality fields.
8. A decision gate for candidate-specific B1/B2 equivalence work.

Region medians are not assumed to add to the composite median. Attribution is a
normalized engineering index, not an accounting decomposition of end-to-end
time.

## 4. Scaling model

For each `method × model_seed × metric`, the analysis fits:

```text
log2(metric) = intercept
             + beta_depth * log2(depth)
             + beta_width * log2(width)
             + beta_batch * log2(batch_size)
```

It publishes `2 ** beta` as the multiplier per factor doubling, together with
`R²` and the maximum absolute log2 residual. The model omits interactions and
is a descriptive sensitivity summary rather than a universal complexity law.

## 5. Engineering continuation rules

The preregistered thresholds remain:

- FixedPred speedup: at least 15%;
- Strict speedup: at least 20%.

The baseline decision gate uses only the Amdahl upper-bound proxy for the
normalized `local_state_vjp + parameter_vjp` share. Passing this proxy gate
authorizes implementation and candidate-specific numerical gates, not the full
B1/B2 matrix before trajectory equivalence passes.

## 6. Locality boundary

B0 sealed aggregates support region-cost attribution. Multidimensional
locality claims require separate structural fields:

- dependency radius;
- graph span/modules;
- independent lifetime;
- feedback operator;
- orchestration barriers.

When these fields are absent, locality claims remain blocked and the analysis
records that limitation rather than filling it with assumptions.

## 7. Derived outputs

The software pipeline creates a separate `analysis-v1` root containing:

- paired configuration and matrix summaries;
- seed/configuration/matrix region attribution;
- paired region summaries;
- seed-level and matrix scaling summaries;
- `analysis_summary.json`;
- `analysis_metadata.json`;
- four deterministic PDF figures;
- bounded Russian and English reports;
- `SHA256SUMS`.

Metadata records the analysis source commit and fixed generation timestamp. The
output root must not already exist. The sealed input is verified before and
after analysis.

# Stage 3B B0: statistical and engineering analysis pipeline

[Русская версия](stage3b-b0-analysis-pipeline.md)

## Purpose

`stage3b_b0_analysis.py` implements read-only analysis of the published
`sealed-v1` evidence. CLI:

```bash
python scripts/analyze_stage3b_b0.py \
  --evidence-root results/stage-3/profiling/b0/sealed-v1 \
  --output-root results/stage-3/profiling/b0/analysis-v1 \
  --source-commit <merged-analysis-implementation-commit> \
  --generated-at-utc <frozen-UTC-timestamp>
```

## Gates

Before calculation, the pipeline verifies:

- exact `SHA256SUMS` equality;
- no missing or unexpected files;
- the published seal claim boundary;
- 96 cells, 480 region rows, 48 pairs, and 32 configuration rows;
- the complete factorial matrix and three seeds per configuration;
- integrity flags and absence of non-finite events.

After outputs are written, the sealed input is verified again. Output inside
`sealed-v1` is rejected.

## Analytical limitations

- statistical unit: `model_seed`;
- independent `n=3` per configuration;
- p-values are not used for superiority claims;
- the configuration matrix is descriptive;
- region shares are normalized within the sum of region medians;
- scaling models omit interactions;
- full Stage 3B remains incomplete.

## Software/evidence separation

The recommended sequence uses two commits:

1. a software commit with the module, CLI, tests, and frozen analysis contract;
2. after merge, a separate evidence commit with generated `analysis-v1`.

This lets metadata record the merged analysis implementation commit and enables
exact committed-tree verification before publication.

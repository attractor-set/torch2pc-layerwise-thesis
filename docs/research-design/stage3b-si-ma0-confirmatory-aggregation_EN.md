# Stage 3B SI-MA0: confirmatory aggregation and evidence

[Russian version](stage3b-si-ma0-confirmatory-aggregation.md)

## Status

This document defines the separate analysis and publication stage after all ten
immutable `SI-MA0` confirmatory cells have completed.

[Execution](../glossary_EN.md#term-execution) is frozen at:

```text
execution source commit = 03016e68ecc7a850da7148d676f47acfb07cc99e
image revision          = 03016e68ecc7a850da7148d676f47acfb07cc99e
contract id             = stage3b-si-ma0-v2
model seeds             = 0..9
validation batch ids    = 0,1,2
```

Aggregation code is introduced in a dedicated implementation commit. Generated
confirmatory [evidence](../glossary_EN.md#term-evidence) is recorded in a subsequent evidence commit. The original
working attempts are neither modified nor included in the implementation commit.

## Principles

The package follows the repository principles:

- protocol-first: thresholds, regions, seeds, and estimands remain frozen;
- the independent unit is the independently trained model identified by
  `model_seed`;
- negative results are retained;
- scientific failure does not justify replacement or retuning;
- execution source/image are separated from aggregation source;
- raw records are combined without post-result filtering;
- Russian is the primary documentation language and English is maintained as a
  paired version;
- conclusions remain limited to the registered checkpoints, batches, and ROCm
  lane.

## Inputs

Aggregation consumes:

1. ten directories under
   `results/stage-3/si-ma0/working/confirmatory/seed-<n>/primary-03016e68ecc7`;
2. each cell's internal `SHA256SUMS`;
3. the external ten-[attempt](../glossary_EN.md#term-attempt) ledger and seed archives;
4. the frozen [checkpoint](../glossary_EN.md#term-checkpoint) inventory;
5. the full cohort archive;
6. the frozen `STAGE3B-SI-MA0-CONTRACT.json`;
7. the sealed A1 prerequisite controls;
8. the sealed ROCm `OBS-OH0` joint-VJP timing summary.

`OBS-OH0` is descriptive context only. Its overhead budget does not replace the
five-percent `COST-MA0` threshold because the estimands and execution paths
differ.

## Completeness checks

Before evidence is created, the aggregator verifies:

- exactly seeds `0..9`;
- one execution source commit and image revision;
- `contract_id = stage3b-si-ma0-v2`;
- three validation batches per seed;
- all cell decisions are made;
- the test split was not accessed;
- all internal SHA256 manifests pass;
- all external seed archives and hashes pass;
- checkpoints and checkpoint inventory pass;
- required counts equal `3000/600/3600/150/7500/52500/70`;
- CSV schemas agree across seeds;
- no timing keys are missing or duplicated;
- stored region sums and accounting residuals are independently reproduced.

If any completeness check fails, the output directory is removed in full and no
evidence package is produced.

## Primary estimands

For [model seed](../glossary_EN.md#term-model-seed) `m` and region `r`:

```text
s[m,r] = sum(region_device_time[m,r]) /
         sum(state_inference_total_device_time[m])
```

Aggregation first occurs within seed over batch, repetition, and measured step.
Across the ten seeds, the package reports:

- every seed-level value;
- median;
- Q1, Q3, and IQR;
- mean;
- a 95% percentile-bootstrap CI for the median;
- an additional 95% bootstrap CI for the mean;
- `10000` repeats;
- bootstrap seed `20260715`;
- `model_seed` as the only resampling unit.

The unattributed residual is published separately and is not redistributed among
the seven frozen regions.

## Global gates

The global decision is computed only after full aggregation:

```text
si_ma0_passed =
    prerequisites_verified
    and REC-MA0
    and OBS-MA0
    and VER-MA0
    and COST-MA0
    and CMP-MA0
```

`COST-MA0` is independently recomputed over 7500 measured steps and 150
repetition-level aggregates using the frozen `rho <= 0.05` threshold, minimum
step fraction `0.99`, and repetition fraction `1.0`.

## Outputs

Evidence is generated under:

```text
results/stage-3/si-ma0/confirmatory/
```

The package contains combined mandatory raw records, seed summaries, primary
cost shares, bootstrap statistics, residual statistics, a source-attempt
manifest, descriptive `OBS-OH0` context, the global summary and decision,
paired Russian/English reports, and the package-level `SHA256SUMS`.

## Interpretation boundary

The similarity between the accounting residual and previously measured ROCm
joint-VJP observer overhead may be reported as descriptive scale consistency. It
does not establish identical quantities and does not alter formal `COST-MA0`.

With complete evidence and at least one failed gate, the final state is `fail`,
not `inconclusive`. Such a result does not open `NCZ/ECZ/TNZ` interpretation or
the subsequent B1/B2 gates.

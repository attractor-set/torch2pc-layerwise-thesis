# Stage 3B matched-profiling descriptive-analysis protocol

[Русская версия](STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS.md)

Status: **protocol frozen after data collection but before comparative results;
analysis execution remains closed**.

Freeze date: 2026-07-21.

## 1. Epistemic boundary

This document is not a preregistration made before data collection. The
288-cell campaign is already complete and sealed. It is a
`post-collection/pre-analysis` freeze: it defines estimands, aggregation order,
and the [Pareto-admissibility](../../docs/glossary_EN.md#term-pareto-admissibility)
rule before software analysis, comparative tables, figures, or candidate
selection are produced.

The machine-readable protocol builder verifies only:

- identity and checksums of the sealed
  [evidence](../../docs/glossary_EN.md#term-evidence);
- the publication boundary;
- categorical matrix identity, row counts, and required fields;
- thresholds registered previously in the Stage 3 protocol.

The builder does not use observed timing, memory, or locality values to choose
rules. This code boundary does not convert a post-collection freeze into a
pre-data preregistration.

## 2. Immutable source

Analysis may read only:

```text
results/stage-3/profiling/matched/
  stage3b-matched-profiling-e1dcfb2-v1/
```

The source is bound to:

```text
release_tag=stage3b-matched-profiling-evidence-v1
release_commit=21ddfb8840674871f0b9d888b36397f5cf0e111b
execution_source_commit=e1dcfb26823e1191b98d2aa2a598499b13197583
image_digest=sha256:3c269b4278026b5b69968b3265b506ce626f2baf693859989de3371d639da4d0
```

`SHA256SUMS`, `SEALED-SHA256SUMS`, `seal.json`, compact tables, and the
compressed locality stream must be verified before and after analysis. The
sealed source is never modified or regenerated.

## 3. Design and statistical unit

The matrix contains:

```text
3 candidates
× 2 methods
× 4 depths
× 2 widths
× 2 batch sizes
× 3 model seeds
= 288 cells
```

The three candidates within one configuration form one matched block. There are
96 blocks. The independent statistical unit is `model_seed`, with values `70`,
`71`, and `72`.

Five repetitions, measured steps, locality events, and configurations do not
increase the independent sample size. At `n=3`, the protocol does not produce
p-values, bootstrap intervals, or statistical-superiority claims.

## 4. Registered aggregation order

The order cannot change after the freeze:

1. measured steps to repetition;
2. repetitions to cell;
3. candidate to `stage2_baseline` within a matched block;
4. three model seeds to a configuration summary;
5. 16 configurations to a descriptive `candidate × method` summary.

At repetition level, the protocol uses:

- medians for time, observer cost, saved tensors, and VJP counts;
- maxima for peak memory, graph span, and dependency radius.

At cell level, it uses medians of repetition summaries for time and structural
counters and maxima across repetitions for memory and maximum structural
boundaries. These rules are already reflected in the sealed compact tables;
analysis must not reaggregate raw steps with different functions.

Across the three model seeds, the protocol reports median, minimum, maximum,
and directional-consistency count. A summary over 16 configurations is
strictly descriptive and does not treat configurations as independent
replicates.

## 5. Estimands

### 5.1. Primary estimand

For each candidate within a matched block:

```text
device_time_ratio = candidate_device_time / baseline_device_time
device_time_reduction = 1 - device_time_ratio
device_speedup = 1 / device_time_ratio
```

`device_time_reduction` is the primary quantity for the continuation rule.

### 5.2. Secondary estimands

Relative to `stage2_baseline`, analysis calculates:

- host-time ratio;
- peak-allocated-memory ratio;
- peak-reserved-memory ratio.

### 5.3. Structural estimands

Relative to `stage2_baseline`, analysis calculates:

- saved-tensor-byte ratio;
- state-VJP-count ratio;
- graph-span ratio;
- dependency-radius ratio.

The compressed locality event stream additionally supports only these
registered diagnostics:

- event count per measured step;
- median logical-edge count per event;
- graph-module coverage fraction;
- maximum graph-island count;
- orchestration barriers per measured step;
- graph-lifetime distribution.

Observer cost is reported separately, is not subtracted from primary timing,
and is excluded from the primary Pareto vector.

## 6. Descriptive scaling model

For every `candidate × method × model_seed` combination, analysis fits one model
for each of the seven Pareto ratio metrics:

```text
log2(candidate_to_baseline_ratio) = intercept
                                  + beta_depth * log2(depth)
                                  + beta_width * log2(width)
                                  + beta_batch * log2(batch_size)
```

No interactions are included. The output reports `2 ** beta`, R², and maximum
absolute residual on the log2 scale. The model is a descriptive sensitivity
summary, not a universal complexity law.

## 7. Pareto rule

The decision unit is `candidate × method × depth × width × batch_size` after
three-seed aggregation.

Seven components are minimized:

1. median device-time ratio;
2. median peak-allocated-memory ratio;
3. median peak-reserved-memory ratio;
4. median saved-tensor-byte ratio;
5. median state-VJP-count ratio;
6. median graph-span ratio;
7. median dependency-radius ratio.

`stage2_baseline` is included among the alternatives. Alternative A dominates
B when every A component is no greater than the corresponding B component plus
`1e-12`, and at least one A component is smaller by more than `1e-12`.

The rule has no hidden scalarization and does not imply a single winner. A
missing, zero, or negative denominator fails the corresponding configuration
closed.

## 8. Engineering continuation rule

Previously registered thresholds remain unchanged:

- `FixedPred`: at least 15% device-time reduction;
- `Strict`: at least 20% device-time reduction;
- at most 3% device-time regression in any seed;
- at most 15% peak-allocated-memory growth;
- at most 15% peak-reserved-memory growth.

A configuration qualifies only when all thresholds pass and the candidate is
Pareto-admissible.

For each `candidate × method` pair:

- `retain`: all 16 configurations qualify;
- `conditional`: 1–15 configurations qualify;
- `reject_or_revise`: no configuration qualifies.

For a candidate overall:

- `retain`: both methods are `retain`;
- `conditional`: at least one method is `retain` or `conditional`;
- `reject_or_revise`: both methods are `reject_or_revise`.

This is an engineering continuation decision for the next registered screen.
It does not authorize policy activation, `EX-IF0`, execution control, or a
superiority claim.

## 9. Missingness, outliers, and sensitivity

The protocol forbids:

- exclusion after result inspection;
- trimming or winsorization;
- imputation;
- increasing independent sample size with repetitions or configurations.

A missing cell, duplicate key, non-finite metric, or nonpositive denominator
fails analysis closed.

Registered sensitivity outputs are:

- directional consistency across seeds;
- leave-one-seed-out descriptive summaries;
- secondary host-time comparison;
- separate allocated- and reserved-memory conclusions.

## 10. Registered outputs

Future analysis creates one new empty output root exactly once and fails closed if
the root already exists or contains files. It produces exactly 18 top-level files:

```text
paired_block_metrics.csv                 192 rows
configuration_summary.csv                 64 rows
candidate_method_summary.csv               4 rows
pareto_membership.csv                      96 rows
locality_cell_summary.csv                 288 rows
scaling_seed_effects.csv                   84 rows
analysis_metadata.json
analysis_summary.json
engineering_decision.json
REPORT.md
REPORT_EN.md
SHA256SUMS
```

It also creates six deterministic PDFs covering device-time ratios, memory
ratios, structural-cost ratios, scaling effects, Pareto membership, and seed
consistency.

The exact file set, checksums, and linkage to the input seal are validated
before analysis sealing.

## 11. Open and closed work

After this protocol merges, only a separate analysis implementation and
synthetic validation are allowed. Analysis execution requires a new
machine-readable authorization bound to this protocol's SHA-256.

Until that authorization exists:

```text
analysis_execution_permitted=false
analysis_results_present=false
results_publication_permitted=false
release_publication_permitted=false
ex_if0_opened=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

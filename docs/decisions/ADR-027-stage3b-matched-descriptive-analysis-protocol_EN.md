# ADR-027: freeze the matched-profiling descriptive-analysis protocol

[Русская версия](ADR-027-stage3b-matched-descriptive-analysis-protocol.md)

- **Status:** accepted
- **Date:** 2026-07-21

## Context

The sealed [evidence](../glossary_EN.md#term-evidence) contains 288 cells, 96
matched blocks, 1,440 repetition rows, and the complete locality-event stream.
An immutable tag and draft release are bound to merge commit
`21ddfb8840674871f0b9d888b36397f5cf0e111b`.

Data collection is complete, but comparative analysis has not run. Estimands,
aggregation, Pareto membership, and B1/B2 decision rules must be fixed before
computing results. The freeze must not be represented as a preregistration made
before data collection.

The repository already contains an early partial implementation in
`stage3b_matched_analysis.py`. It is not an authorized implementation of this
protocol and must be reconciled in a separate PR.

## Decision

Create a deterministic package:

```text
experiments/frozen/stage3b-matched-descriptive-analysis-v1/
  protocol.json
  SHA256SUMS
```

The protocol freezes:

- sealed-evidence identity and checksums;
- `model_seed` as the independent unit and a no-pseudoreplication rule;
- immutable aggregation order;
- primary, secondary, and structural estimands;
- a descriptive [scaling](../glossary_EN.md#term-scaling) model for seven explicitly listed ratios;
- a seven-dimensional
  [Pareto-admissibility](../glossary_EN.md#term-pareto-admissibility) rule without
  hidden scalarization;
- 15% `FixedPred`, 20% `Strict`, 3% maximum-regression, and 15% memory-growth
  thresholds;
- formal `retain / conditional / reject_or_revise` outcomes;
- missingness, sensitivity, and an exact 18-file future output set;
- closed [execution](../glossary_EN.md#term-execution), publication, `EX-IF0`, and policy-activation boundaries.

The protocol builder may inspect only source identity, structure, and the
categorical matrix. It does not use observed timing, memory, or locality values
to choose rules.

## Consequences

Benefits:

- comparative decisions become machine-reproducible;
- previously registered thresholds cannot change after collection;
- repetitions and configurations do not inflate independent `n=3`;
- mixed evidence can yield `conditional` rather than a forced single winner;
- sealed input remains read-only.

Limitations:

- this is a post-collection/pre-analysis freeze, not a pre-data preregistration;
- strong inferential claims are prohibited with three seeds;
- a seven-dimensional Pareto set may contain multiple alternatives;
- the early partial analysis implementation requires a separate implementation
  PR.

## Boundary after merge

```text
matched_profiling_analysis_protocol_frozen=true
matched_profiling_analysis_implementation_open=true
matched_profiling_analysis_execution_open=false
matched_profiling_analysis_results_present=false
results_publication_permitted=false
release_publication_permitted=false
ex_if0_opened=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

The next permitted step is protocol implementation against synthetic data and a
fail-closed `--check` path. Running against sealed results requires a separate
machine-readable authorization.

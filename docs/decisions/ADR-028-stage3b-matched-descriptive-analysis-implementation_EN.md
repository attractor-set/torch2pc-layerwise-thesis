# ADR-028: implement the matched-profiling descriptive analysis

[Русская версия](ADR-028-stage3b-matched-descriptive-analysis-implementation.md)

- **Status:** accepted
- **Date:** 2026-07-21

## Context

ADR-027 froze the `post-collection/pre-analysis` contract before comparative
results were calculated. The early `stage3b_matched_analysis.py` implementation
created only four files, aggregated configurations directly, and did not
implement the registered [scaling](../glossary_EN.md#term-scaling), [Pareto-admissibility](../glossary_EN.md#term-pareto-admissibility), locality, or
`retain / conditional / reject_or_revise` rules.

After ADR-027 merged, implementation and synthetic validation became permitted,
but [execution](../glossary_EN.md#term-execution) against sealed
[evidence](../glossary_EN.md#term-evidence) remains closed until a separate
machine-readable authorization is merged.

## Decision

Replace the early analyzer with a registered computational engine that:

- validates the complete matrix of 288 cells, 96 matched blocks, and 1,440
  repetition rows;
- produces exactly 192 paired rows, 64 [configuration](../glossary_EN.md#term-configuration) rows, four
  `candidate × method` summaries, 96 Pareto-set rows, 288 locality rows, and 84
  scaling rows;
- implements the seven-dimensional Pareto rule with mandatory
  `stage2_baseline` inclusion and `1e-12` tolerance;
- applies the 15%, 20%, 3%, and 15% thresholds only in the registered order;
- streams either a plain or `Zstandard`-compressed locality-event stream;
- calculates the six registered locality diagnostics without loading the whole
  stream into memory;
- creates exactly 18 deterministic files, including six PDFs, two reports, and
  `SHA256SUMS`;
- verifies input checksums before and after reading;
- uses an atomic new output directory and fails closed if that directory already
  exists;
- leaves the output unsealed and prohibits publication, `EX-IF0`, policy
  activation, and superiority claims.

The synthetic path requires a dedicated full-fixture marker. The public sealed-
evidence function intentionally raises until a separate execution authorization
is merged. The command-line script accepts only a synthetic fixture directory.

## Consequences

Benefits:

- the complete ADR-027 contract is exercised against a full synthetic matrix;
- the `steps → repetitions → cells → blocks → seeds → configurations`
  aggregation order is explicit;
- outputs are byte-reproducible for a fixed generation time;
- inputs remain read-only;
- a future execution authorization can reuse the tested engine without changing
  estimands or schemas.

Limitations:

- synthetic output is not evidence and cannot be preserved as a scientific
  result;
- the complete compressed locality stream has not yet been processed from the
  sealed source;
- implementation does not open analysis or create a B1/B2 decision;
- execution requires a separate request freeze, authorization, and new output
  directory.

## Boundary after merge

```text
matched_profiling_analysis_protocol_frozen=true
matched_profiling_analysis_implementation_complete=true
matched_profiling_analysis_synthetic_validation=pass
matched_profiling_analysis_execution_open=false
matched_profiling_analysis_results_present=false
analysis_output_evidence=false
results_publication_permitted=false
release_publication_permitted=false
ex_if0_opened=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

The next permitted step is a separate machine-readable execution-request freeze
and fail-closed authorization bound only to the immutable ADR-027 source.

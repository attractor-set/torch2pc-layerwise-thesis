# ADR-029: harden matched descriptive analysis before execution

[Русская версия](ADR-029-stage3b-matched-descriptive-analysis-preexecution-hardening.md)

- **Status:** accepted
- **Date:** 2026-07-21

## Context

ADR-027 froze the protocol, and ADR-028 implemented the computational engine
and validated it on the complete synthetic matrix. An independent post-merge
audit identified three boundaries that must be closed before a separate
[execution](../glossary_EN.md#term-execution) authorization for sealed
[evidence](../glossary_EN.md#term-evidence):

1. the shared engine accepted `source_kind`, but metadata and summary always
   received synthetic statuses and `analysis_execution_authorized=false`;
2. compact tables were checked for size and coverage, but their mutual
   consistency across 288 cells, 1,440 repetitions, and 96 summary rows was not
   proven;
3. the `Zstandard` test replaced the decoder with `cat` and did not validate a
   real compressed frame.

No numerical results have been computed, sealed-source execution remains
closed, and the draft release remains unpublished.

## Decision

Before freezing the execution request, harden the registered engine as
follows.

### Source provenance

Introduce a closed set of source profiles:

- `synthetic_fixture` emits
  `generated_unsealed_synthetic_implementation_output`, summary status
  `synthetic_implementation_validation_only`, and
  `analysis_execution_authorized=false`;
- `sealed_evidence` is reserved for the future separately authorized path and
  emits `generated_unsealed_authorized_analysis_output`, summary status
  `generated_unsealed_authorized_descriptive_analysis`, and
  `analysis_execution_authorized=true`;
- an unknown `source_kind` fails closed.

This decision does not open the public sealed-source path.

### Compact-table consistency

Before calculating ratios or decisions, the engine must verify:

- exact identity of block, [candidate](../glossary_EN.md#term-candidate), method, [configuration](../glossary_EN.md#term-configuration), `model_seed`,
  graph-lifetime mode, feedback operator, and [fallback](../glossary_EN.md#term-fallback) status between every
  cell row and its five repetitions;
- exact repetition coverage `0..4` for each of the 288 cells;
- agreement of timing, observer, saved-tensor, and `VJP` medians and of memory,
  span, and dependency-radius maxima between the 1,440 repetition rows and the
  288 cell rows;
- exactly 96 unique `profiling_summary.csv` rows;
- exact coverage of three `model_seed` values in every summary configuration;
- agreement of medians and maxima between the 288 cell rows and the 96 summary
  rows.

Numeric comparison uses `rel_tol=1e-12` and `abs_tol=1e-9` and fails closed on
any mismatch.

### Real `Zstandard` canary

The synthetic test creates a real `Zstandard` frame with the system `zstd`
binary and verifies streaming through the same decoder path intended for the
archived locality stream.

## Consequences

Positive:

- a future authorized output cannot carry synthetic provenance;
- compact evidence is validated as one internally consistent system rather
  than three independently plausible tables;
- `Zstandard` decoding is tested on a real frame;
- estimands, thresholds, the 18 outputs, and the frozen ADR-027 SHA-256
  identities remain unchanged.

Limitations:

- the `sealed_evidence` profile is not an execution authorization by itself;
- the public sealed-analysis function still raises `execution is closed`;
- analysis results, sealing, and publication remain absent;
- separate request freezing and authorization remain mandatory.

## Boundary after merge

```text
matched_profiling_analysis_protocol_frozen=true
matched_profiling_analysis_implementation_complete=true
matched_profiling_analysis_preexecution_hardening=complete
matched_profiling_analysis_compact_consistency=verified_synthetic_and_sealed_fixture
matched_profiling_analysis_zstandard_canary=real_frame_pass
matched_profiling_analysis_execution_open=false
matched_profiling_analysis_results_present=false
analysis_output_evidence=false
results_publication_permitted=false
release_publication_permitted=false
test_dataset_access=false
```

The next permitted step is a separate machine-readable execution-request and
authorization freeze, not a change to the computational estimands.

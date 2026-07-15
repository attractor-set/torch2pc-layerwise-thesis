# ADR-011: Derived evidence seal for Stage 3B B0

[Русская версия](ADR-011-stage3b-b0-derived-evidence-seal.md)

## Context

The Stage 3B B0 canonical lane completes 96 ROCm/float32 cells and preserves
raw records as non-[evidence](../glossary_EN.md#term-evidence) [execution](../glossary_EN.md#term-execution) artifacts. Those records deliberately
retain `evidence=false`, `full_campaign_complete=false`, and
`results_publication_permitted=false`: the runner must not execute the
experiment and authorize publication claims in the same lifecycle boundary.

After the corrective process-isolation run, the raw output was copied to a
persistent archive and frozen by `SHA256SUMS`. Manually changing terminal
records, `lane-state.json`, or the authorization chain would break provenance.

## Decision

Stage 3B B0 receives a separate read-only validation, aggregation, and sealing
pipeline.

The pipeline:

1. requires the expected [execution](../glossary_EN.md#term-execution) source commit, sealing implementation
   source commit, image digest, and SHA-256 of the `SHA256SUMS` file;
2. verifies that the inventory exactly covers every archive file;
3. validates the freeze, ROCm preflight, authorization, manifest snapshot,
   lane state, run terminal, 96 attempts, and 96 process records;
4. independently revalidates numerical integrity and region completeness;
5. produces compact seed-level and paired aggregate tables;
6. creates a new content-addressed derivative bundle outside the raw archive;
7. rechecks the raw archive before committing the derivative output.

The raw archive remains immutable and retains its original non-[evidence](../glossary_EN.md#term-evidence) flags.
Only the derivative seal records:

- `evidence=true`;
- `full_b0_campaign_complete=true`;
- `results_publication_permitted=true`;
- `full_stage3b_campaign_complete=false`.

The final field makes clear that only the B0 [baseline](../glossary_EN.md#term-baseline) [candidate](../glossary_EN.md#term-candidate) is complete,
not the broader Stage 3B [candidate](../glossary_EN.md#term-candidate) campaign.

## Statistical unit

`model_seed` remains the statistical unit. Repetitions, measured steps, and
[profiling](../glossary_EN.md#term-profiling) regions are repeated observations within a seed. FixedPred/Strict
paired tables are joined by depth, width, batch size, and [model seed](../glossary_EN.md#term-model-seed).

## Consequences

- [Execution](../glossary_EN.md#term-execution) code does not change publication status.
- Raw records and Stage 3A [evidence](../glossary_EN.md#term-evidence) remain unchanged.
- Compact derived tables can be versioned and published separately from the
  large raw archive.
- Any archive mutation, missing [attempt](../glossary_EN.md#term-attempt), failed terminal, process-isolation
  violation, or numerical-integrity failure blocks sealing.
- The seal records separate [execution](../glossary_EN.md#term-execution) and sealing implementation commits.
- Re-sealing the same archive with the same sealing commit produces the same
  `seal_digest`.

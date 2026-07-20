# ADR-019: confirmatory `EQ-B1` infrastructure opening

[Русская версия](ADR-019-stage3b-b1-confirmatory-opening.md)

## Status

Accepted: implementation ready, experimental
[execution](../glossary_EN.md#term-execution) closed.

## Context

ADR-018 froze confirmatory `EQ-B1` as 120 matched pairs:

```text
2 lanes × 2 methods × 3 model seeds × 10 validation batches = 120 pairs
```

Preregistration does not create a safe launch path. Execution additionally
requires reproducible batch freezing, a frozen request, independent checks of
both execution lanes, explicit authorization, an append-only
[attempt](../glossary_EN.md#term-attempt) lifecycle, and fail-closed
[integrity sealing](../glossary_EN.md#term-integrity-sealing) of the [evidence](../glossary_EN.md#term-evidence).

## Decision

A dedicated confirmatory B1 infrastructure is added. Results from the historical
engineering smoke cannot be treated as confirmatory evidence.

### Validation-batch freeze

The first 10 full 256-item batches are exported from the deterministic
`shuffle=False` validation loader reconstructed from the common Stage 2 BP
protocol. Every batch has a separate tensor file, file SHA-256, content SHA-256,
manifest, batch index, and `split=validation` marker.

All 10 paths and all 10 content SHA-256 values must be distinct. The test split
is neither created nor read.

### Frozen request

The request contains exactly 120 unique `pair_id` values, three
[checkpoints](../glossary_EN.md#term-checkpoint), 10 batches, one resolved
[configuration](../glossary_EN.md#term-configuration) digest, and the Torch2PC
commit.

The project source commit and immutable image SHA-256 are not embedded in the
request itself, because that would create a cyclic reference to a commit that
must include the request file. Their exact values are bound later by the
[runtime](../glossary_EN.md#term-runtime)-authorization freeze after the request is merged and the image is
built. Freezing the request does not authorize execution.

### Runtime authorization

Authorization requires a clean project worktree at the exact source commit,
verification of all registered files, one image SHA-256, independent
`cpu_float64` and `rocm_float32` checks, the exact operator acknowledgement, and
a new output root under `/tmp`.

Authorization domains are separated. The full campaign uses mode
`confirmatory`, authorizes 120 pairs, and requires
`AUTHORIZE_STAGE3B_B1_CONFIRMATORY_120_MATCHED_PAIRS_CPU_FLOAT64_ROCM_FLOAT32`.
The engineering smoke uses mode `engineering_smoke`, authorizes only 12 pairs,
and requires
`AUTHORIZE_STAGE3B_B1_ENGINEERING_SMOKE_12_PAIRS_CPU_FLOAT64_ROCM_FLOAT32_NON_EVIDENCE`.
A token from one mode is rejected by the other mode.

### Execution and recovery

Each pair uses append-only history with a maximum of 2 attempts. Only
infrastructure, operator, and system interruptions are retryable. Correctness,
scientific, provenance, and unknown failures are non-retryable.

Resume continues never-started pairs and retries eligible failures only when
`retry_failed` is explicit. An orphaned started attempt may be closed as a
system interruption only through a separate command, with no lane lock and the
exact operator acknowledgement.

### Engineering smoke

A dedicated smoke uses 12 pairs with `validation_batch_index=0`. It requires a
separate output root and authorization, remains `evidence=false`, and cannot be
sealed as confirmatory evidence.

### Evidence sealing

A positive seal requires 120/120 registered pairs, exactly one successful final
attempt per pair, no running attempts, admissible retry history, successful
`STRUCT-B1`, `NUM-B1`, `TRAJ-B1`, `OBS-B1`, `PROV-B1`, and valid SHA-256
registries.

The final scientific decision must have
`decision_id=EQ-B1-CONFIRMATORY`, `scope=confirmatory`, and `status=pass`. It is
followed by a separate derived `matched-profiling-admission.json` record with
`decision_id=EQ-B1`, `matched_pairs_expected=120`,
`matched_pairs_observed=120`, and the SHA-256 of the scientific decision. The
derived record does not replace the scientific decision and is used only by
the future matched-[profiling](../glossary_EN.md#term-profiling) admission path.

## Opening boundary

This ADR and implementation do not open execution. Frozen batches, the frozen
request, a new image, two lane checks, authorization, and a passing engineering
smoke remain absent after merge. `EQ-B2` and 288-cell
[profiling](../glossary_EN.md#term-profiling) remain closed.

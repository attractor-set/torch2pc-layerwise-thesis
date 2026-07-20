# ADR-022: opening the confirmatory `EQ-B2` infrastructure

[Русская версия](ADR-022-stage3b-b2-confirmatory-opening.md)

- Status: accepted — implementation ready, [execution](../glossary_EN.md#term-execution) closed
- Date: 2026-07-20

## Context

[ADR-021](ADR-021-stage3b-b2-confirmatory-preregistration_EN.md) froze
confirmatory `EQ-B2` as 120 matched triples and 240 direct comparisons:

```text
2 lanes × 2 methods × 3 model seeds × 10 validation batches = 120 triples
```

Each triple starts from one shared snapshot for `stage2_baseline`,
`isolated_layer_vjp`, and `composite_vjp`. It requires two comparisons:
`stage2_baseline ↔ composite_vjp` and
`isolated_layer_vjp ↔ composite_vjp`.

Preregistration does not create a safe [runtime](../glossary_EN.md#term-runtime)
path. The confirmatory campaign still needs a deterministic request,
provenance verification for the reused B1 inputs, separate smoke and
confirmatory authorization domains, an append-only [attempt](../glossary_EN.md#term-attempt) lifecycle,
recovery after admissible interruptions, and fail-closed
[integrity sealing](../glossary_EN.md#term-integrity-sealing).

## Decision

Add separate confirmatory B2 infrastructure. It reuses the frozen B1
validation batches and checkpoints byte-for-byte and performs no new data
selection.

### Deterministic request freeze

The freeze script must create exactly 120 unique `triple_id` values and bind:

- lanes `cpu_float64` and `rocm_float32`;
- methods `FixedPred` and `Strict`;
- `model_seed=0,1,2`;
- `validation_batch_index=0..9`;
- the three B1 checkpoints and ten B1 batches with their existing SHA-256 values;
- the B2 preregistration, [candidate](../glossary_EN.md#term-candidate) implementation, and equivalence-harness contracts;
- the sealed `EQ-B1-CONFIRMATORY` decision and derived B1 admission;
- `test_dataset_access=false`.

No new batches or checkpoints are exported. Request creation does not authorize
execution.

### Separated authorization

Authorization requires a clean worktree at the exact source commit, an
immutable image, both lane preflights, an empty dedicated output root, and an
exact operator acknowledgement.

The full campaign uses the `confirmatory` domain, authorizes 120 triples and
240 comparisons, and requires:

```text
AUTHORIZE_STAGE3B_B2_CONFIRMATORY_120_MATCHED_TRIPLES_240_COMPARISONS_CPU_FLOAT64_ROCM_FLOAT32
```

The non-[evidence](../glossary_EN.md#term-evidence) engineering check uses the `engineering_smoke` domain, only
12 triples and 24 comparisons, and a distinct acknowledgement:

```text
AUTHORIZE_STAGE3B_B2_ENGINEERING_SMOKE_12_MATCHED_TRIPLES_24_COMPARISONS_CPU_FLOAT64_ROCM_FLOAT32_NON_EVIDENCE
```

A token from one domain is invalid in the other domain.

### Execution and recovery

Each triple has an append-only history and at most two attempts. Retry is
allowed only after an infrastructure, operator, or system interruption.
Correctness, scientific, provenance, and unknown failures are non-retryable.

Resume selects incomplete triples. Retrying a failed triple requires explicit
`resume` and `retry_failed`. An orphaned running attempt may be closed as a
system interruption only through a separate command, with no lane lock and an
exact operator acknowledgement.

Primary numerical and trajectory checks use `observer_mode=no_hooks`.
Structural replay uses `counters_only` and does not replace primary equivalence
verification.

### Evidence sealing

A positive decision requires:

```text
matched_triples_expected=120
matched_triples_observed=120
pairwise_comparisons_expected=240
pairwise_comparisons_observed=240
failed_pair_count=0
sealed=true
status=pass
```

Successful `STRUCT-B2`, `NUM-B2`, `TRAJ-B2`, `OBS-B2`, and `PROV-B2` gates are
also mandatory, together with exactly one completed last attempt per triple,
no running attempts, and valid SHA-256 registries.

The scientific decision uses `decision_id=EQ-B2-CONFIRMATORY` and
`scope=confirmatory`. It is followed by a separate
`matched-profiling-admission.json` record with `decision_id=EQ-B2`, the
scientific-decision SHA-256, and the complete 120/240 counters.

The derived record permits only a new versioned scientific-admission freeze
for [matched profiling](../glossary_EN.md#term-matched-profiling). It does not
authorize the 288-cell execution.

## Opening boundary

This ADR and its code mean only:

```text
implementation_ready_execution_closed
```

After merge, the following are still absent:

- a frozen B2 confirmatory request;
- an immutable image;
- CPU/ROCm preflight results;
- issued authorization;
- a passing engineering smoke;
- results for the 120 triples;
- sealed `EQ-B2-CONFIRMATORY`;
- derived `EQ-B2` admission;
- a refreshed 288-cell profiling request and manifest.

The opening branch creates no files under `experiments/frozen/**` or
`results/**`, starts no measurements, changes no historical B2 smoke artifact,
and does not open the test split. The next stage is a separate prospective B2
confirmatory request-freeze PR.

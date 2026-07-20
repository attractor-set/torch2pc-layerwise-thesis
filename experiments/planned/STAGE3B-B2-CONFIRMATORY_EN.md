# Stage 3B B2 confirmatory equivalence

[Русская версия](STAGE3B-B2-CONFIRMATORY.md)

## Status

`preregistered_execution_closed`. This document freezes the confirmatory B2
design. No frozen request, immutable image, runtime authorization, or results
are present.

## Prerequisite

Confirmatory B1 is complete and sealed:

```text
EQ-B1-CONFIRMATORY
scope=confirmatory
matched_pairs=120/120
failed_pairs=[]
sealed=true
status=pass
```

The existing B2 smoke contains only `12` triples and `24` comparisons and
remains engineering evidence. It does not open production matched profiling.

## Matrix

| Factor | Values |
|---|---|
| lane | `cpu_float64`, `rocm_float32` |
| method | `FixedPred`, `Strict` |
| model seed | `0`, `1`, `2` |
| validation batch index | `0..9` |

Full cardinality:

```text
2 × 2 × 3 × 10 = 120 matched triples
```

The [model seed](../../docs/glossary_EN.md#term-model-seed) remains the
independent unit. Lane, method, batch, comparison, layer, sweep, and tensor
component are nested units.

## Input reuse

Confirmatory B2 must reuse unchanged:

- the ten-batch registry at
  `experiments/frozen/stage3b-b1-confirmatory/validation-batches.json`;
- batch artifacts and manifests for indices `0..9`;
- the three checkpoints and resolved configs from the frozen B1 confirmatory
  request;
- the B1 confirmatory decision and derived admission at their registered
  SHA-256 digests.

No new batch selection is performed. The test split is neither created nor
read.

## Triple and comparison contract

A triple ID is constructed from `lane`, `method`, `model_seed`, and
`validation_batch_index`. Identical model state, buffers, beliefs, optimizer,
RNG state, and batch are restored before all three candidates.

Every triple produces exactly two registered comparisons:

1. `stage2_baseline ↔ composite_vjp`;
2. `isolated_layer_vjp ↔ composite_vjp`.

The design therefore requires `120` unique triple IDs and `240` pairwise
comparisons. Primary equivalence uses `no_hooks`; structural replay is a
separate `counters_only` lane.

## Lifecycle

Attempt history is append-only. At most two attempts are permitted per triple.
Retry is allowed only after infrastructure, operator interruption, or system
interruption. Correctness, scientific, provenance, and unknown failures are
non-retryable and block sealing.

## Execution opening

A separate opening branch must create and verify:

1. a frozen request with `120` unique triple IDs;
2. exact paths and SHA-256 digests for reused B1 batches/checkpoints;
3. the B1 confirmatory decision/admission and B2 contracts;
4. source commit, Torch2PC commit, and immutable image digest;
5. separate `cpu_float64` and `rocm_float32` preflights;
6. explicit runtime authorization;
7. a dry-run reporting `pending=120` on an empty output root.

Confirmatory execution remains closed until all requirements pass.

## Decision and next transition

A positive scientific decision must contain:

```text
decision_id=EQ-B2-CONFIRMATORY
scope=confirmatory
confirmatory_equivalence_executed=true
matched_triples_expected=120
matched_triples_observed=120
pairwise_comparisons_expected=240
pairwise_comparisons_observed=240
failed_pairs=[]
sealed=true
status=pass
```

A separate derived `EQ-B2` admission with the same confirmatory counts is then
created. Only that admission permits a new version of the matched-profiling
request/manifest. It does not authorize 288-cell execution, `EX-IF0`, QWake-PC,
or test-split access.

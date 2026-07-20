# Stage 3B B1 confirmatory equivalence

[Русская версия](STAGE3B-B1-CONFIRMATORY.md)

## Status

`preregistered_execution_closed`. This document freezes the confirmatory B1
design; the execution request, batch artifacts, image, authorization, and
results are absent.

## Matrix

| Factor | Values |
|---|---|
| lane | `cpu_float64`, `rocm_float32` |
| method | `FixedPred`, `Strict` |
| model seed | `0`, `1`, `2` |
| validation batch index | `0..9` |

Full cardinality:

```text
2 × 2 × 3 × 10 = 120 matched pairs
```

Model seed is the independent unit. All other levels are nested.

## Batch freeze

Batch indices `0..9` identify the first ten distinct full batches from the
validation loader reconstructed from the common Stage 2 BP data protocol with
`shuffle=False`. Every batch is stored separately and verified by its own
SHA-256. One batch cannot occupy multiple indices. The same batches are shared
across model seeds, methods, and lanes. `include_test=false` and
`test_split_access=false` are mandatory.

## Pair contract

A pair ID is derived from `lane`, `method`, `model_seed`, and
`validation_batch_index`. Identical model state, buffers, beliefs, optimizer,
RNG, and batch are restored before the reference and B1 arms. Primary
equivalence uses `no_hooks`; structural replay runs separately in
`counters_only`.

Thresholds and registered components are inherited unchanged from
`STAGE3B-B1-CONTRACT.json`. Threshold retuning, outlier deletion, and scientific
failure replacement are forbidden.

## Execution opening

A later opening branch must create and validate:

1. ten batch artifacts and ten manifests;
2. a frozen request with 120 unique pair IDs;
3. source commit, Torch2PC commit, and immutable image digest;
4. checkpoint path/SHA-256 for seeds `0..2`;
5. runtime preflight and explicit authorization;
6. a dry run with `pending=120`.

Until these conditions are met, `EQ-B1-CONFIRMATORY` remains closed.

## Decision

A positive decision must contain:

```text
scope=confirmatory
confirmatory_equivalence_executed=true
registered_pair_count=120
observed_pair_count=120
failed_pair_count=0
sealed=true
status=pass
```

It opens only confirmatory B2. Matched profiling remains closed until a positive
confirmatory `EQ-B2` decision is also available.

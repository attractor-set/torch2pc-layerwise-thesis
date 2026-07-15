# Experiment protocol

[Русская версия](experiment-protocol.md)

```text
static checks
-> asset preparation
-> pinned Torch2PC
-> C0/C1 CPU
-> C0/C1 GPU
-> validation-only pilot matrix
-> pilot-configuration freeze
-> final paired runs
-> diagnostics
-> report preparation
```

Paired comparisons use matching split indices, `model_seed`, data-loader seed,
optimizer, batch size, dtype, image, Torch2PC commit, and [dataset](glossary_EN.md#term-dataset) files.

A failed [run](glossary_EN.md#term-run) receives a unique `run_id`, retains failure metadata, and does not
overwrite a previous run. A retry does not remove the original failure.

Final [execution](glossary_EN.md#term-execution) remains blocked when control-check files or the pilot-freeze
manifest are missing.

## Repeated test access

Only one completed final run is allowed for a given source commit, authorized
[configuration](glossary_EN.md#term-configuration), and `model_seed`. A technically failed [attempt](glossary_EN.md#term-attempt) may be retried,
but its record and cause remain visible. A new successful run after a code or
[configuration](glossary_EN.md#term-configuration) change is a separate experiment and does not replace the original
[confirmatory analysis](glossary_EN.md#term-confirmatory-analysis).

## Observation artifacts

Validation and test predictions are stored per example with original indices,
true labels, predictions, and probabilities. This permits independent
verification of aggregate metrics without executing the [checkpoint](glossary_EN.md#term-checkpoint) again.

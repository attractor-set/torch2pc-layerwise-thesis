# Experiment protocol

[Русская версия](experiment-protocol.md)

The sequence is static checks, asset preparation, pinned Torch2PC, CPU/GPU controls, validation-only pilot, pilot freeze, final paired runs, diagnostics, and reporting. Failed attempts remain visible under unique run IDs.

## Repeated test access

Only one completed final run is accepted for the same source commit, resolved
configuration, and model seed. Failed attempts remain visible. Validation and
test outputs are stored as per-sample prediction artifacts with original
dataset indices.

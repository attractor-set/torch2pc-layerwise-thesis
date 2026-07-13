# STAGE3-001: locality, approximation, and scaling

[Русская версия](STAGE3-001.md)

## Status

Design-ready; execution blocked.

## Baseline

- Stage 2 execution: `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2`;
- Stage 2 publication: `bb435432a65b76b7fc4f383b566b9a372fc346ae`;
- Torch2PC: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

## Matrices

- profiling: 288 short matched cells;
- screening pilot: 48 parameterized validation-only terminal cells;
- final template: up to 80 cells after freeze.

## Implementation-start acceptance

`make stage3-ready` passes, the deterministic plan is generated, Stage 3 is
absent from `TRAINING_STAGES`, and the final template keeps test disabled.

# EXP-001: Infrastructure smoke test

[Русская версия](EXP-001.md)


## Purpose

Confirm that the controlled environment, data loading, model construction,
training step, validation, checkpoint, and manifest pipeline execute.

## Configuration

- Stage: smoke
- Dataset: MNIST
- Model: LeNet-classic
- Method: BP
- Seed: 0

## Acceptance criteria

- Process exits successfully.
- No NaN or Inf occurs.
- `metrics.json`, `history.csv`, `checkpoint.pt`,
  `environment.json`, and `manifest.json` are created.
- Registry status is `completed`.

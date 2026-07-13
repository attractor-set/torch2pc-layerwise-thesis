# ADR-005: post-pilot final execution freeze

- Status: accepted
- Date: 2026-07-13
- Decision point: after the validation-only pilot, before `pilot-freeze` and before any final-test access

## Context

The pilot completed all 96 planned cells without failures and selected
`FixedPred(eta=0.1, n=10)` and `Strict(eta=0.05, n=20)`. Precision planning
returned an advisory value of 10 complete pairs. The final seed count therefore
remains 10 (`0-9`) under the preregistered rule and is not increased in response
to the direction of the pilot effect.

Infrastructure limitations were identified before final execution: methods were
run in blocks, the full registry was both pilot evidence and the mutable final
log, and the environment lock did not expose a combined configuration-tree
hash.

## Decision

1. Create an immutable `final_execution_plan.json` before `pilot-freeze`.
2. Counterbalance method order with deterministic SHA-256 ranking within every
   dataset/model/seed combination.
3. Preserve a dedicated `pilot_registry_snapshot.csv` while keeping
   `experiments/registry.csv` as the append-only final log.
4. Support safe final resumption by skipping completed cells in the current
   cohort while retaining failed attempts for documented technical reruns.
5. Synchronize the GPU before every timed epoch and record mean/median epoch
   time, runtime device, PyTorch/HIP versions, and peak GPU memory.
6. Add a combined configuration-tree SHA-256 to the environment lock.

## Unchanged design elements

- primary dataset: FashionMNIST;
- secondary dataset: MNIST;
- primary metric: macro F1;
- primary contrasts: FixedPred vs BP and Strict vs BP;
- equivalence margin: `+-0.01`;
- final seeds: `0-9`;
- selected hyperparameters;
- one test evaluation per completed final run.

## Consequences

The changes improve execution-order reproducibility, resumption safety, and
computational telemetry. They do not reselect hyperparameters or alter the
confirmatory hypotheses. Training-time comparisons remain secondary and
descriptive; equal-wall-clock analysis remains a separately labelled diagnostic
stage.

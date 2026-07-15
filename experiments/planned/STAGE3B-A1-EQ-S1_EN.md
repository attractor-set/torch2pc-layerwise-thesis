# Stage 3B A1 — EQ-S1: reduced shortcut

## Status

The protocol is frozen. Implementation and experimental results are absent.

## Research question

Does a separate opt-in reduced shortcut reproduce backpropagation endpoint gradients and parameters after one identical stateless SGD step in the registered pinned environment?

## Compared paths

Reference:

- standard backpropagation;
- the existing registered BP evaluator;
- observer mode `no_hooks`.

Candidate:

- a separate reduced-shortcut evaluator;
- its own entry point;
- no delegation to the reference BP evaluator as a ready-made black box;
- no delegation to the complete iterative FixedPred loop as a ready-made black box;
- canonical BP, FixedPred, and Strict paths remain unchanged.

Iterative FixedPred is not the EQ-S1 reference. Its direct comparison with the reduced shortcut is performed separately in EQ-S2.

## Invariants

Reference and candidate use:

- identical initial `state_dict`;
- identical batch;
- identical loss function and reduction;
- identical dtype and device;
- identical optimizer configuration;
- separate model and optimizer clones;
- identical RNG state where applicable;
- fully disabled instrumentation;
- observer mode `no_hooks`.

## Endpoint

Primary endpoint:

1. named parameter gradients;
2. parameters after one identical optimizer step.

Optimizer:

- SGD;
- learning rate `0.001`;
- momentum `0.0`.

## Numerical threshold policy

The same preregistered lane-specific policy as EQ-S0 is used.

CPU:

- `min_cosine = 0.99999`;
- `max_relative_l2 = 1e-7`;
- `zero_atol = 1e-12`.

ROCm:

- `min_cosine = 0.999`;
- `max_relative_l2 = 1e-3`;
- `zero_atol = 1e-7`.

Thresholds are not retuned after inspecting EQ-S1 results.

## Execution scope

Canonical execution is performed only in the controlled Docker image.

Smoke:

- model seeds `0, 1, 2`;
- `1` batch per seed;
- Docker CPU;
- Docker/ROCm.

Confirmatory control after a successful smoke:

- model seeds `0, 1, 2`;
- `10` batches per seed;
- Docker CPU;
- Docker/ROCm.

Model seed remains the independent experimental unit. Batches are repeated control observations within a seed.

## Pass criteria

EQ-S1 passes only when all conditions hold:

- all compared tensors are finite;
- all endpoint-gradient components pass the registered lane-specific thresholds;
- all parameters after the optimizer step pass the registered lane-specific thresholds;
- every run has `passed = true`;
- Docker image provenance matches the experiment source commit;
- the Torch2PC revision matches across execution lanes;
- the candidate does not alter canonical BP, FixedPred, or Strict behavior.

## Stop rules

For any failed or non-finite comparison:

- EQ-S1 receives status `failed`;
- EQ-S2 remains closed;
- observer controls remain closed;
- the reduced shortcut is not enabled in canonical execution;
- the cause is investigated without retuning the registered thresholds.

## Claim boundary

A positive EQ-S1 establishes only endpoint-gradient equivalence and equivalence after one stateless SGD step in the registered environment and evaluated sample.

EQ-S1 does not establish:

- hidden-state trajectory equivalence;
- full training-trajectory equivalence;
- equivalence for Adam or momentum SGD;
- equivalence between the reduced shortcut and iterative FixedPred;
- observer non-interference;
- runtime benefit.

## Evidence policy

Working outputs are stored under the ignored `working/` directory.

After a successful confirmatory control, a separate immutable evidence package is created with a manifest, bounded claim, and SHA-256. Sealed EQ-S0 evidence remains unchanged.

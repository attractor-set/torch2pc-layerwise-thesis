# Stage 3B A1 — EQ-S2: iterative FixedPred versus joint-VJP shortcut

## Status

The protocol is frozen. EQ-S2 implementation and experimental results are absent.

## Research question

Does the opt-in joint-VJP reduced shortcut reproduce endpoint gradients and parameters after one identical stateless SGD step relative to the existing iterative FixedPred path with `eta = 1` and `n = len(model)` in the registered pinned environment?

## Role of EQ-S2

EQ-S2 closes the third side of the triangular control:

\[
\mathrm{BP}
\overset{\mathrm{EQ-S0}}{\equiv}
\mathrm{iterative\ FixedPred}
\]

\[
\mathrm{BP}
\overset{\mathrm{EQ-S1}}{\equiv}
\mathrm{joint\mbox{-}VJP\ shortcut}
\]

\[
\mathrm{iterative\ FixedPred}
\overset{\mathrm{EQ-S2}}{\equiv}
\mathrm{joint\mbox{-}VJP\ shortcut}
\]

EQ-S2 is a direct comparison and does not rely only on a transitive inference from EQ-S0 and EQ-S1.

## Compared paths

### Reference

- the existing iterative FixedPred path;
- `eta = 1`;
- `inference_steps = len(model)`;
- feed-forward initialization;
- observer mode `no_hooks`;
- fully disabled instrumentation.

### Candidate

- the opt-in joint-VJP reduced shortcut;
- one joint state-and-parameter VJP for every top-level layer;
- one detached graph island per layer;
- no `loss.backward()` in the candidate;
- no iterative FixedPred loop in the candidate;
- observer mode `no_hooks`;
- fully disabled instrumentation.

Canonical BP, FixedPred, and Strict paths remain unchanged.

## Input-state invariants

Reference and candidate use:

- identical initial `state_dict`;
- identical batch;
- identical loss function and reduction;
- identical dtype and device;
- identical optimizer configuration;
- separate model clones;
- separate optimizer clones;
- identical RNG state where applicable;
- identical training/evaluation mode;
- identical buffers;
- identical input-preparation sequence.

## Endpoint

Primary endpoint:

1. named parameter gradients;
2. parameters after one identical optimizer step;
3. tensor optimizer state;
4. scalar optimizer state.

Optimizer:

- SGD;
- learning rate `0.001`;
- momentum `0.0`.

With `momentum = 0.0`, tensor optimizer state is expected to be absent. This limitation is recorded in the claim boundary.

## Candidate structural contract

For the current `lenet_classic`, the expected values are:

- `top_level_layers = 6`;
- `joint_vjp_calls = 6`;
- `graph_islands = 6`;
- `parameterized_layers = 5`;
- `parameter_components = 10`;
- `one_call_per_layer = true`;
- `loss_backward_used_by_candidate = false`;
- `iterative_fixedpred_loop_used_by_candidate = false`.

A structural-contract violation fails the run independently of endpoint metrics.

## Numerical threshold policy

The same registered lane-specific policy as EQ-S0 and EQ-S1 is used.

### CPU

- `min_cosine = 0.99999`;
- `max_relative_l2 = 1e-7`;
- `zero_atol = 1e-12`;
- dtype: `torch.float64`.

### ROCm

- `min_cosine = 0.999`;
- `max_relative_l2 = 1e-3`;
- `zero_atol = 1e-7`;
- dtype: `torch.float32`.

Thresholds are not retuned after inspecting EQ-S2 results.

## Execution scope

Canonical execution is performed only in the controlled Docker image.

### Smoke

- model seeds `0, 1, 2`;
- `1` batch per seed;
- Docker CPU;
- Docker/ROCm.

### Confirmatory control

After a successful smoke:

- model seeds `0, 1, 2`;
- `10` batches per seed;
- Docker CPU;
- Docker/ROCm.

Model seed remains the independent experimental unit. Batches are repeated control observations within a seed.

## Pass criteria

EQ-S2 passes only when all conditions hold:

- all compared tensors are finite;
- all endpoint-gradient components pass the registered lane-specific thresholds;
- all parameters after the optimizer step pass the registered lane-specific thresholds;
- optimizer state satisfies the registered stateless SGD contract;
- every run has `passed = true`;
- the candidate structural contract is satisfied;
- Docker image provenance matches the experiment source commit;
- the Torch2PC revision matches across execution lanes;
- sealed EQ-S0 and EQ-S1 evidence remain unchanged.

## Stop rules

For any failed or non-finite comparison:

- EQ-S2 receives status `failed`;
- observer controls remain closed;
- the reduced shortcut is not enabled in canonical execution;
- registered thresholds are not retuned;
- the cause is investigated in a separate diagnostic patch;
- a repeated confirmatory run is permitted only after a new source commit and a separate provenance record.

## Supported claim

A positive EQ-S2 supports the claim that, in the registered pinned environment, iterative FixedPred with `eta = 1` and `n = len(model)` and the joint-VJP reduced shortcut produce equivalent endpoint gradients and parameters after one stateless SGD step in the registered CPU and ROCm sample.

## Claim boundary

EQ-S2 does not establish:

- equality of intermediate hidden-state trajectories;
- full training-trajectory equivalence;
- equivalence for Adam or momentum SGD;
- runtime benefit;
- memory benefit;
- observer non-interference;
- correctness of active QWake;
- universal equivalence outside the registered architecture and environment.

## Evidence policy

Working outputs are stored under the ignored `working/` directory.

After a successful confirmatory control, a separate immutable evidence package is created:

- CPU summary and records;
- ROCm summary and records;
- manifest;
- bounded claim;
- SHA-256;
- a separate evidence commit;
- annotated tag `stage3b-a1-eq-s2-v1`.

Sealed EQ-S0 and EQ-S1 evidence remain unchanged.

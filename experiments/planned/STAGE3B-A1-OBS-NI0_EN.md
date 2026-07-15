# Stage 3B A1 — OBS-NI0: passive-observer non-interference

## Status

The protocol is frozen. Passive-observer implementation and experimental results are absent.

## Preceding equivalence gates

OBS-NI0 is opened only after successful sealing of:

- EQ-S0: BP versus iterative FixedPred;
- EQ-S1: BP versus the joint-VJP reduced shortcut;
- EQ-S2: iterative FixedPred versus the joint-VJP reduced shortcut.

Registered baseline:

- repository commit: `826d8666c2d38b011253582c84abd7f0fdeb916e`;
- EQ-S0 tag: `stage3b-a1-eq-s0-v1`;
- EQ-S1 tag: `stage3b-a1-eq-s1-v1`;
- EQ-S2 tag: `stage3b-a1-eq-s2-v1`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

## Research question

Does enabling a passive observer change endpoint gradients, parameters after one optimizer step, optimizer state, model buffers, or RNG state relative to an otherwise identical execution with the observer disabled?

## Role of OBS-NI0

OBS-NI0 evaluates only the computational non-interference of the observer.

A positive result means that the registered passive observer did not change the evaluated endpoints in the registered environment and sample.

OBS-NI0 does not evaluate:

- usefulness of the captured signals;
- correctness of their mechanistic interpretation;
- runtime overhead;
- memory overhead;
- the full training trajectory;
- active observers or intervention logic.

Runtime and memory overhead belong to the separate OBS-OH0 gate.

## Observer contract

The passive observer is a read-only instrumentation layer.

During the observed execution path it:

- does not modify model parameters;
- does not modify model buffers;
- does not modify optimizer state;
- does not modify input tensors;
- does not modify the computation graph;
- does not call `backward()`;
- does not call additional `torch.autograd.grad`;
- does not call `optimizer.step()`;
- does not use in-place operations on observed tensors;
- does not invoke random operations;
- does not use observed values to control the computation path.

Tensor payload is captured as a detached copy:

    captured = tensor.detach().clone()

During the observed forward/reverse path, the observer does not call the following on payload tensors:

- `.item()`;
- `.numpy()`;
- `.cpu()`;
- device synchronization added specifically for logging;
- disk writes.

Moving payload to CPU and serialization are permitted only after completion of the observed computation path.

## Observer schema freeze

The exact capture points and payload roles are frozen in the implementation source commit before the first controlled smoke run.

The implementation source commit must include:

- a constant `observer_schema_id`;
- an ordered list of expected payload roles;
- the expected number of records per layer and run;
- naming rules for layer and tensor records;
- cleanup rules;
- structural-completeness unit tests.

After the first controlled execution, the schema is not changed without a new source commit and a new preregistered evidence version.

OBS-NI0 uses the payload only to evaluate structure and the passive-observer contract. Scientific interpretation of payload is outside this gate.

## Compared arms

### Arm A — iterative FixedPred

Reference:

- iterative FixedPred;
- `eta = 1`;
- `inference_steps = len(model)`;
- feed-forward initialization;
- observer disabled.

Candidate:

- the same iterative FixedPred path;
- identical `eta`, inference steps, and initialization;
- passive observer enabled.

### Arm B — joint-VJP reduced shortcut

Reference:

- the opt-in joint-VJP reduced shortcut;
- one joint state-and-parameter VJP per top-level layer;
- observer disabled.

Candidate:

- the same joint-VJP reduced shortcut;
- passive observer enabled.

Canonical BP, FixedPred, and Strict implementations remain unchanged.

## Paired-execution contract

Each reference/candidate pair uses:

- an identical initial model `state_dict`;
- separate model clones;
- an identical input batch;
- identical targets;
- an identical loss function and reduction;
- an identical dtype;
- an identical device;
- an identical training/evaluation mode;
- identical model buffers;
- an identical optimizer configuration;
- separate optimizer instances;
- an identical RNG snapshot before each paired path.

Before reference execution, the following states are saved:

- Python RNG state;
- NumPy RNG state;
- PyTorch CPU RNG state;
- ROCm RNG state for every available device.

The same snapshot is restored before candidate execution.

The input batch is created before the paired RNG snapshot and is not loaded again between reference and candidate.

## Endpoint comparisons

For every arm, the following are compared:

1. named parameter gradients;
2. parameters after one identical optimizer step;
3. tensor optimizer state;
4. scalar optimizer state;
5. model buffers;
6. post-execution Python RNG state;
7. post-execution NumPy RNG state;
8. post-execution PyTorch CPU RNG state;
9. post-execution ROCm RNG state;
10. observer lifecycle cleanup.

Optimizer:

- SGD;
- learning rate `0.001`;
- momentum `0.0`.

With `momentum = 0.0`, tensor optimizer state is expected to be absent. This limitation is recorded in the claim boundary.

## Buffer comparison

Named buffer key sets must match exactly.

Floating-point buffers use the lane-specific numerical thresholds.

Integer, boolean, and categorical buffers use exact equality.

The absence of model buffers is an acceptable result and is explicitly recorded in the summary.

## RNG comparison

The observer must not consume RNG.

Post-execution RNG states for reference and candidate must match exactly after restoration of the identical pre-execution snapshot.

ROCm RNG is compared separately for every available device.

## Observer payload invariants

For every captured tensor:

- it is a detached copy;
- `requires_grad = false`;
- `grad_fn is None`;
- its value is finite;
- its shape satisfies the registered schema;
- dtype metadata matches the source tensor;
- device metadata matches the source tensor;
- a layer identifier is present;
- a tensor role is present;
- the record key is unique within the run.

After completion of the run:

- all expected capture points are present;
- duplicate records are absent;
- the observer lifecycle is closed;
- registered hooks or handles are removed;
- observer storage contains no references to a live autograd graph.

A payload-invariant violation fails the run independently of endpoint equivalence.

## Numerical threshold policy

The same lane-specific numerical policy as EQ-S0, EQ-S1, and EQ-S2 is used.

### CPU

- dtype: `torch.float64`;
- `min_cosine = 0.99999`;
- `max_relative_l2 = 1e-7`;
- `zero_atol = 1e-12`.

### ROCm

- dtype: `torch.float32`;
- `min_cosine = 0.999`;
- `max_relative_l2 = 1e-3`;
- `zero_atol = 1e-7`.

Thresholds are not retuned after inspection of OBS-NI0 results.

## Execution scope

Canonical execution is performed only in the controlled Docker image.

### Smoke

- model seeds: `0, 1, 2`;
- batches per seed: `1`;
- arms: FixedPred and joint-VJP;
- lanes: Docker CPU and Docker/ROCm.

### Confirmatory control

After a successful smoke:

- model seeds: `0, 1, 2`;
- batches per seed: `10`;
- arms: FixedPred and joint-VJP;
- lanes: Docker CPU and Docker/ROCm.

Model seed is the independent experimental unit. Batches are repeated control observations within a seed.

## Expected minimum confirmatory endpoint-evidence volume

On every execution lane:

- `30` paired runs for the FixedPred arm;
- `30` paired runs for the joint-VJP arm;
- `60` paired runs in total;
- `600` endpoint-gradient comparisons;
- `600` parameter-after-step comparisons;
- `1200` endpoint tensor comparisons.

Across both lanes:

- `120` paired runs;
- `1200` endpoint-gradient comparisons;
- `1200` parameter-after-step comparisons;
- `2400` endpoint tensor comparisons.

Buffer, RNG, and observer-payload records are counted separately and are not included in these endpoint totals.

## Pass criteria

OBS-NI0 passes only when all conditions hold:

- all endpoint tensors are finite;
- all gradient comparisons pass the registered thresholds;
- all parameter-after-step comparisons pass the registered thresholds;
- optimizer tensor state matches;
- optimizer scalar state matches;
- model buffer keys and values match;
- post-execution RNG states match exactly;
- the observer payload schema is complete;
- every captured tensor is detached;
- every payload value is finite;
- duplicate observer records are absent;
- observer cleanup is complete;
- every run in both arms has `passed = true`;
- CPU provenance is verified;
- ROCm provenance is verified;
- the source commit is identical across execution lanes;
- the Torch2PC revision is identical across execution lanes;
- sealed EQ-S0, EQ-S1, and EQ-S2 evidence remain checksum-valid.

## Stop rules

For any failed or non-finite comparison:

- OBS-NI0 receives status `failed`;
- OBS-OH0 remains closed;
- SI-MA0 remains closed;
- the observer is not enabled in canonical execution;
- registered thresholds are not retuned;
- the cause is investigated in a separate diagnostic patch;
- a repeated confirmatory run requires a new source commit;
- a changed observer schema requires a new evidence version.

## Supported claim

A positive OBS-NI0 supports the claim that the registered passive observer did not change endpoint gradients, parameters after one stateless SGD step, optimizer state, model buffers, or RNG state for iterative FixedPred and the joint-VJP reduced shortcut in the registered CPU/ROCm sample.

## Claim boundary

OBS-NI0 does not establish:

- non-interference across the full training trajectory;
- non-interference for stateful optimizers;
- absence of runtime overhead;
- absence of memory overhead;
- correctness of captured-signal interpretation;
- causal validity of PC-CATM;
- universal applicability outside the registered architecture and environment.

## Evidence policy

Working outputs are stored in the ignored `working/` directory.

After a successful confirmatory control, a separate immutable package is created:

- CPU summaries and records;
- ROCm summaries and records;
- an observer schema manifest;
- an evidence manifest;
- a bounded claim;
- SHA-256;
- a separate evidence commit;
- annotated tag `stage3b-a1-obs-ni0-v1`.

Sealed EQ-S0, EQ-S1, and EQ-S2 evidence remain unchanged.

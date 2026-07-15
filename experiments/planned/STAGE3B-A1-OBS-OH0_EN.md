# Stage 3B A1 — OBS-OH0: passive-observer overhead

## Status

The protocol is frozen. The benchmark runner and experimental results are absent.

OBS-OH0 is opened only after OBS-NI0 has passed, been sealed, and been published.

## Registered baseline

- repository evidence commit: `f80d070d79982f6420dce00d504c60dbdf1abc1b`;
- OBS-NI0 implementation commit: `3cbda083bc5747732a51295da9a4494ffde48436`;
- OBS-NI0 tag: `stage3b-a1-obs-ni0-v1`;
- passive-observer schema: `stage3b-a1-obs-ni0-first-forward-io-v1`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

The sealed EQ-S0, EQ-S1, EQ-S2, and OBS-NI0 evidence packages are immutable prerequisites.

## Research question

What are the runtime and memory overheads of the registered passive observer relative to an otherwise identical observer-disabled execution path for:

1. iterative FixedPred;
2. the joint-VJP reduced shortcut?

The additional engineering question is whether the overhead remains within a preregistered budget sufficient to proceed to SI-MA0.

## Role of OBS-OH0

OBS-OH0 is a bounded-overhead control.

It does not test computational non-interference; that property was already evaluated by OBS-NI0. It does not claim that the observer has zero cost. A positive result means that the cost of the registered observer was measured validly and remained within the registered engineering budget in the registered environment and sample.

OBS-OH0 does not evaluate:

- usefulness of the captured signals;
- mechanistic interpretation of the payload;
- full-training overhead;
- overhead for stateful optimizers;
- overhead for other architectures or batch sizes;
- active observers or intervention logic;
- causal validity of PC-CATM.

## Frozen measurement object

Only the observer sealed by OBS-NI0 is measured:

- schema id: `stage3b-a1-obs-ni0-first-forward-io-v1`;
- top-level layers: `6`;
- roles: `layer_input`, `layer_output`;
- capture policy: the first forward invocation of every top-level layer;
- records per observer-on execution: `12`;
- payload copy: `tensor.detach().clone()`;
- later forward invocations are counted but not captured again;
- observer lifecycle ends by removing every registered hook.

A change to the schema, capture points, payload roles, copy policy, or cleanup policy requires a new preregistration and evidence version.

## Compared arms

### Arm A — iterative FixedPred

Reference:

- iterative FixedPred;
- `eta = 1`;
- `inference_steps = len(model) = 6`;
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

Canonical BP, FixedPred, Strict, and joint-VJP implementations remain unchanged.

## Benchmark schema freeze

Before the first controlled smoke run, the implementation source commit must freeze:

- constant `benchmark_schema_id = stage3b-a1-obs-oh0-v1`;
- exact measured-region contract;
- ordered execution records;
- paired-order rule;
- warm-up policy;
- timing-repeat count;
- memory-worker protocol;
- device-synchronization policy;
- metric units;
- aggregation rules;
- pass criteria;
- output schemas;
- provenance checks;
- unit tests.

After the first controlled execution, the benchmark schema is not changed without a new source commit and a new preregistered evidence version.

## General paired-execution contract

Every observer-off / observer-on pair uses:

- an identical initial model `state_dict`;
- a separate fresh model clone for every execution;
- an identical input batch and targets;
- an identical loss function and reduction;
- an identical dtype and device;
- an identical model mode;
- an identical RNG snapshot;
- an identical Torch2PC checkout;
- an identical controlled Docker image;
- an identical CPU thread configuration;
- no disk writes or console logging inside the measured region.

The input batch is loaded before the paired snapshot. Model cloning, device transfer, input loading, result validation, DataFrame construction, and serialization are outside the measured region.

Before every paired execution, the following states are restored:

- Python RNG state;
- NumPy RNG state;
- PyTorch CPU RNG state;
- ROCm RNG state for every available device.

## Separation of timing and memory phases

Runtime and memory are measured in separate phases.

The reason is that an RSS sampler, allocator queries, peak-stat resets, and memory diagnostics themselves create overhead and must not enter the primary timing estimand.

### Timing phase

The timing phase contains only the matched observer lifecycle and computational path.

### Memory phase

The memory phase runs in separate isolated worker processes and is not used for runtime inference.

Timing records and memory records are not merged into a single time estimate.

## Timing measured-region contract

For every execution:

1. the model clone, inputs, and targets are fully prepared;
2. gradients are cleared;
3. the paired RNG snapshot is restored;
4. on ROCm, an external `torch.cuda.synchronize()` is executed;
5. `start_ns = time.perf_counter_ns()` is recorded;
6. the reference enters a matched no-op observer context or the candidate registers passive-observer hooks;
7. only the registered backward path of the corresponding arm is executed;
8. the context closes; the candidate removes the hooks;
9. on ROCm, an external `torch.cuda.synchronize()` is executed;
10. `end_ns = time.perf_counter_ns()` is recorded.

Primary elapsed time:

```text
elapsed_ns = end_ns - start_ns
```

The measured region includes:

- observer setup;
- tensor capture and detached clone;
- observer cleanup;
- the corresponding FixedPred or joint-VJP backward path.

The measured region excludes:

- the dataloader;
- model construction or deepcopy;
- device transfer;
- optimizer construction;
- `optimizer.step()`;
- endpoint comparison;
- payload validation;
- CPU transfer;
- serialization;
- disk I/O;
- benchmark-summary calculation.

`optimizer.step()` is excluded because the observer is already closed and identical extra work would artificially dilute relative overhead.

## ROCm synchronization policy

ROCm kernels and copies must complete before the end timestamp is read.

`torch.cuda.synchronize()` is called symmetrically:

- immediately before `start_ns`;
- immediately before `end_ns`.

Synchronization is not called inside observer hooks and is not treated as an observer operation. It is an external benchmark boundary applied identically to observer-off and observer-on executions.

## Timing warm-up policy

Warm-up is executed on:

- model seed `0`;
- batch index `0`;
- separately for every lane and arm.

The registered number of untimed paired warm-up repetitions is:

- smoke: `1` pair per lane and arm;
- confirmatory: `3` pairs per lane and arm.

Warm-up uses the same alternating-order policy, but its records:

- are marked as `warmup`;
- are excluded from aggregate estimands;
- are excluded from pass criteria.

No additional discretionary exclusion of measured records is allowed.

## Paired order and drift control

Observer-off / observer-on order is balanced deterministically.

For every `(lane, arm, model_seed, batch_index, repeat_index)`:

```text
parity = model_seed + batch_index + repeat_index + arm_index
```

- for even `parity`: observer-off followed by observer-on;
- for odd `parity`: observer-on followed by observer-off.

`arm_index = 0` for FixedPred and `1` for joint-VJP.

The order is recorded in every record. Manual order changes after inspecting results are not allowed.

## Timing metrics

For every measured pair, the following are stored:

- `reference_elapsed_ns`;
- `candidate_elapsed_ns`;
- `runtime_delta_ns`;
- `runtime_ratio`;
- `runtime_overhead_fraction`;
- lane;
- arm;
- model seed;
- batch index;
- repeat index;
- execution order;
- dtype;
- device;
- source commit;
- image identifier;
- Torch2PC commit;
- benchmark schema id;
- observer schema id.

Definitions:

```text
runtime_delta_ns = candidate_elapsed_ns - reference_elapsed_ns
runtime_ratio = candidate_elapsed_ns / reference_elapsed_ns
runtime_overhead_fraction = runtime_ratio - 1
```

Both elapsed values must be positive and finite.

## Timing aggregation

Model seed is the independent experimental unit.

Batches and timing repetitions are repeated engineering observations within a seed and are not treated as independent scientific units.

For every `(lane, arm, seed)`, median `runtime_ratio` is calculated across:

- `10` batches;
- `3` measured paired repetitions per batch;
- `30` paired timing records per seed.

For every `(lane, arm)`, the primary estimand is:

```text
primary_runtime_ratio =
median of the three seed-level median runtime_ratio values
```

The following are also recorded:

- minimum seed-level median;
- maximum seed-level median;
- median absolute `runtime_delta_ns`;
- all raw paired records;
- order-stratified medians for off-first and on-first records.

The arithmetic mean is not the primary runtime estimand. Measured outliers are not removed.

## Memory phase isolation

Every memory execution runs in a fresh worker process inside the same controlled image.

Before the measured region, the worker:

- loads the registered model and batch;
- creates the model clone;
- moves tensors to the registered device;
- restores RNG state;
- stabilizes the device;
- records baseline memory.

Process startup, imports, model construction, data loading, and device transfer are excluded from incremental memory metrics.

Observer-off and observer-on memory executions run in separate fresh workers with identical metadata.

## Payload memory accounting

For candidate execution, exact retained payload size is calculated as:

```text
payload_bytes =
sum(tensor.numel() * tensor.element_size())
```

Payload bytes are counted from captured detached tensors before release.

The following are also recorded:

- record count;
- bytes per role;
- bytes per layer;
- dtype;
- source device;
- shape metadata.

Exactly `12` payload records are expected for every observer-on memory execution.

## CPU memory metrics

The CPU worker uses Linux `/proc/self/status`.

The following are recorded:

- baseline `VmRSS`;
- sampled peak `VmRSS` during the measured region;
- final `VmRSS` before payload release;
- `VmHWM` as a diagnostic process-level value;
- `incremental_peak_rss_bytes`;
- `incremental_final_rss_bytes`.

A dedicated sampler reads `VmRSS` at an interval no greater than `1 ms`.

Definitions:

```text
incremental_peak_rss_bytes =
max(0, sampled_peak_rss_bytes - baseline_rss_bytes)

incremental_final_rss_bytes =
max(0, final_rss_bytes - baseline_rss_bytes)
```

CPU RSS is allocator- and page-sensitive. Exact payload bytes are therefore the primary CPU memory cost, while RSS is a bounded secondary diagnostic.

## ROCm memory metrics

Before the measured region, the ROCm worker:

1. executes `torch.cuda.synchronize()`;
2. records current allocated and reserved bytes;
3. calls `torch.cuda.reset_peak_memory_stats()`;
4. executes the measured region;
5. executes `torch.cuda.synchronize()`;
6. reads peak allocated and peak reserved bytes.

The following are recorded:

- baseline allocated bytes;
- baseline reserved bytes;
- peak allocated bytes;
- peak reserved bytes;
- current allocated bytes before payload release;
- current reserved bytes before payload release;
- incremental peak allocated bytes;
- incremental peak reserved bytes.

Definitions:

```text
incremental_peak_allocated_bytes =
max(0, peak_allocated_bytes - baseline_allocated_bytes)

incremental_peak_reserved_bytes =
max(0, peak_reserved_bytes - baseline_reserved_bytes)
```

`max_memory_allocated` is the primary ROCm allocator metric. Reserved-memory delta is a secondary diagnostic because of caching-allocator granularity.

## Memory aggregation

For the confirmatory memory phase, one isolated observer-off / observer-on pair is executed for every:

- lane;
- arm;
- model seed;
- batch index.

On every lane:

- `3` seeds;
- `10` batches per seed;
- `2` arms;
- `60` paired memory records.

Across both lanes:

- `120` paired memory records.

For every `(lane, arm, seed)`, medians are calculated for:

- payload bytes;
- observer-on minus observer-off incremental peak memory;
- memory-accounting residual.

Primary memory summaries are the median of the three seed-level medians. Raw records are retained in full.

## Registered runtime budget

For every lane and arm, both conditions must hold:

```text
primary_runtime_ratio <= 1.25
max_seed_median_runtime_ratio <= 1.35
```

This corresponds to:

- primary median overhead no greater than `25%`;
- no seed-level median overhead greater than `35%`.

A single measured repeat is not used as an independent failure threshold because of scheduler and clock noise.

The budget is applied separately to:

- CPU FixedPred;
- CPU joint-VJP;
- ROCm FixedPred;
- ROCm joint-VJP.

## Registered memory budget

For every observer-on execution:

```text
payload_bytes <= 67_108_864
```

Thus retained payload does not exceed `64 MiB`.

### CPU bound

For every `(arm, seed)`:

```text
median(candidate_incremental_peak_rss
       - reference_incremental_peak_rss)
<=
median(payload_bytes) + max(8 MiB, 0.25 * median(payload_bytes))
```

### ROCm allocated-memory bound

For every `(arm, seed)`:

```text
median(candidate_incremental_peak_allocated
       - reference_incremental_peak_allocated)
<=
median(payload_bytes) + max(1 MiB, 0.10 * median(payload_bytes))
```

A negative paired memory difference is allowed as allocator noise and is retained without clipping in the raw paired metric. Individual incremental metrics remain non-negative by definition.

ROCm reserved-memory delta and CPU `VmHWM` are descriptive diagnostics without a hard pass threshold.

## Smoke scope

Canonical smoke runs only in the controlled Docker image.

For every lane:

- model seeds: `0, 1, 2`;
- batch index: `0`;
- arms: FixedPred and joint-VJP;
- timing warm-up pairs: `1` per arm;
- measured timing pairs: `3` per seed and arm;
- isolated memory pairs: `1` per seed and arm.

On every smoke lane, the expected volume is:

- `18` measured timing pairs;
- `36` timed executions;
- `6` memory pairs;
- `12` memory workers.

Smoke evaluates schema, synchronization, order balancing, worker isolation, metric validity, and provenance. Smoke results are excluded from confirmatory evidence.

## Confirmatory scope

After successful smoke, every lane uses:

- model seeds: `0, 1, 2`;
- batches per seed: `10`;
- arms: FixedPred and joint-VJP;
- measured timing pairs per batch and arm: `3`;
- isolated memory pairs per batch and arm: `1`;
- lanes: Docker CPU and Docker/ROCm.

On every confirmatory lane, the expected volume is:

- `180` measured timing pairs;
- `360` timed executions;
- `60` memory pairs;
- `120` memory workers.

Across both lanes, the expected volume is:

- `360` measured timing pairs;
- `720` timed executions;
- `120` memory pairs;
- `240` memory workers.

## Correctness guard

Before timing and memory benchmarking, an untimed guard pair is executed for every `(lane, arm, seed, batch)`.

The guard must confirm:

- endpoint gradients satisfy the OBS-NI0 threshold policy;
- observer schema is complete;
- record count equals `12`;
- hooks are removed;
- payload is detached and finite;
- source commit is identical;
- Torch2PC revision is identical;
- RNG state is not changed by the observer;
- model buffers and inputs are unchanged.

A guard failure marks the lane failed. Guard execution is excluded from overhead metrics.

## Provenance contract

Every output records:

- full source Git commit;
- controlled image identifier;
- image revision label;
- branch;
- benchmark schema id;
- observer schema id;
- Torch2PC commit;
- PyTorch version;
- HIP version;
- lane;
- device name;
- dtype;
- CPU thread count;
- visible ROCm devices;
- model architecture;
- batch size;
- model seeds;
- batch indices;
- timing repetitions;
- warm-up count;
- sampler interval.

CPU and ROCm confirmatory outputs must reference one source commit and one benchmark schema.

The Compose runner must explicitly pass the verified:

- `SOURCE_GIT_COMMIT`;
- `EXPERIMENT_IMAGE`.

Inherited shell environment values must not override verified provenance.

## Pass criteria

OBS-OH0 passes only when all of the following hold:

- the OBS-NI0 seal remains checksum-valid;
- benchmark schema was frozen before smoke;
- every correctness guard passes;
- every elapsed value is positive and finite;
- every memory value is an integer and non-negative where required by definition;
- all expected timing and memory records are present;
- duplicate record keys are absent;
- paired order follows the registered parity rule;
- warm-up records are excluded from confirmatory aggregation;
- CPU and ROCm provenance is verified;
- source commit is identical across both lanes;
- Torch2PC revision is identical across both lanes;
- observer schema matches the sealed OBS-NI0 schema;
- all four lane-arm runtime budgets are satisfied;
- payload budget is satisfied;
- CPU memory bound is satisfied for both arms and all seeds;
- ROCm allocated-memory bound is satisfied for both arms and all seeds;
- every confirmatory run has `passed = true`.

## Stop rules

For a correctness-guard failure, invalid measurement, missing record, provenance mismatch, or registered-budget exceedance:

- OBS-OH0 receives status `failed`;
- SI-MA0 remains closed;
- thresholds are not retuned after inspecting results;
- measured records are not removed;
- the cause is investigated in a separate diagnostic patch;
- observer optimization is performed in a separate source commit;
- a new confirmatory run requires a new evidence version;
- an observer-schema change requires returning to OBS-NI0.

OOM, worker crash, non-finite metric, or zero/negative elapsed time is a failed record.

## Supported claim

A positive OBS-OH0 supports the claim that runtime and retained-memory overhead of the registered passive observer for iterative FixedPred and the joint-VJP reduced shortcut remains within the registered engineering budget in the controlled CPU/ROCm confirmatory sample.

## Claim boundary

OBS-OH0 does not establish:

- zero overhead;
- full-training overhead;
- overhead for stateful optimizers;
- overhead for other models, batch sizes, or devices;
- usefulness or interpretability of payload;
- causal validity of PC-CATM;
- universal production suitability.

Runtime and memory results apply only to the registered architecture, batch size, observer schema, software revision, and controlled hardware lanes.

## Evidence policy

Working outputs are stored in the ignored `working/` directory.

After a successful confirmatory control, a separate immutable package is created containing:

- CPU timing records and summaries;
- CPU memory records and summaries;
- ROCm timing records and summaries;
- ROCm memory records and summaries;
- benchmark schema manifest;
- observer schema reference;
- provenance manifest;
- bounded claim;
- SHA-256;
- a separate evidence commit;
- annotated tag `stage3b-a1-obs-oh0-v1`.

The sealed EQ-S0, EQ-S1, EQ-S2, and OBS-NI0 evidence packages remain unchanged.

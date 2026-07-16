# Stage 3B `SI-MA0` — `state_inference` mechanism and cost attribution

[Russian version](STAGE3B-SI-MA0.md)

## Status

The protocol is frozen before executable implementation and before the first
controlled smoke run.

This package preregisters A8 of primary scenario A: model-level mechanism and
cost attribution for canonical `Strict.state_inference`. It does not modify
sealed implementations or evidence from prior gates, execute the experiment,
or authorize computational control.

Contract id:

```text
stage3b-si-ma0-v1
```

## Registered starting point

- base commit: `30de25c50a970fcdb8038fe1ce20273f5efb9b3c`;
- A1 mechanism-controls implementation:
  `69455e6e77e447ff72609d1c8af5fa6136a7e88a`;
- A1 mechanism-controls evidence:
  `474ce9fcac73ff53565f8da91da5688d72b6f475`;
- A1 evidence tag: `stage3b-a1-mechanism-controls-evidence-v1`;
- A1 decision:
  `results/stage-3/a1-mechanism-controls/confirmatory/mechanism-controls-decision.json`;
- Torch2PC commit:
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

Before any controlled execution, the runner must verify:

```text
mechanism_controls_confirmatory_passed = true
core_controls_passed = true
si_ma0_open = true
```

and verify the checksum of the sealed A1 evidence.

## Research question

On the real model-level `Strict.state_inference` path, can the study:

1. decompose the observed state correction into registered canonical
   `PC-CATM` channels;
2. reconstruct the observed correction from those channels within
   prespecified numerical tolerance;
3. show that observation does not alter states, losses, or gradients;
4. bind every layer and sweep to compatible state and Jacobian versions;
5. close `state_inference` time accounting over registered regions;
6. describe the distribution of time, VJPs, saved tensors, graph lifetime,
   and synchronization across mechanisms?

## Role of the package

`SI-MA0` is a validity-and-attribution gate.

A positive result authorizes model-level passive diagnostics for
`NCZ`/`ECZ`/`TNZ` and later, separate B1/B2 checks. It does not itself
establish:

- the frequency or stability of diagnostic classes during training;
- feature utility for deciding whether another exact sweep is needed;
- permission to skip a sweep or layer;
- acceleration of `Strict`;
- sufficiency of a diagnostic quotient space;
- a causal effect of `QWake-PC`;
- superiority of predictive coding over BP.

## Registered object

### Model and checkpoints

```text
dataset = FashionMNIST
split = validation
architecture = lenet_classic
method = Strict
checkpoint = final
model_seeds = 0..9
dtype = float32
device = ROCm
eta = 0.05
inference_steps = 20
batch_size = 256
validation_batch_ids = 0,1,2
shuffle = false
loader_workers = 0
optimizer_step = disabled
parameter_update = disabled
```

Existing final Stage 2 checkpoints are used. The model is not retrained.
Before every observed run, the checkpoint and initial state are restored.

The test loader is not created:

```text
dataset_loader_used = true
test_split_access = false
```

For each batch, hashes are stored for inputs, targets, example indices,
checkpoint, resolved configuration, and split manifest.

### Independent statistical unit

The independent unit is an independently trained model identified by
`model_seed`.

Batch, layer, sweep, channel, VJP, saved tensor, and technical repetition are
nested observations and are not treated as independent models.

## Execution lanes and scopes

### Smoke

After the implementation commit is frozen, engineering checks run on:

```text
CPU Docker: model_seed=0, validation_batch_id=0
ROCm Docker: model_seed=0, validation_batch_id=0
```

Smoke validates schemas, required fields, numerical reconstruction, test-split
protection, and timer operation. Smoke is excluded from confirmatory evidence
and cannot be used to retune thresholds.

### Confirmatory

The primary confirmatory lane is:

```text
controlled Docker/ROCm
model_seeds = 0..9
validation_batch_ids = 0,1,2
```

After the first controlled confirmatory output, the following are prohibited:

- threshold retuning;
- replacement of a model seed or batch;
- deletion of finite or nonfinite records;
- repetition selection based on results;
- changing the registered regions;
- changing the canonical-channel definition.

## Registered observer modes

For an identical checkpoint and batch, the following modes run:

```text
no_hooks
instrumented_disabled
counters_only
tensor_summaries
full_attribution
```

`no_hooks` is the numerical reference.

All modes use identical weights, inputs, targets, RNG snapshots, `eta`, sweep
count, layer order, and initial belief state. Serialization occurs after the
measured section.

Primary region-time attribution uses `counters_only`. `tensor_summaries` and
`full_attribution` support mechanism reconstruction and overhead measurement,
but their absolute time does not replace canonical-path time.

## `state_inference` decomposition

Seven mutually exclusive regions are registered:

```text
inference_setup
lower_prediction_and_error
upper_state_vjp
component_aggregation
belief_update
sweep_bookkeeping
inference_finalize
```

Definitions:

- `inference_setup` — initial belief states and per-call structures, excluding
  dataset and checkpoint loading;
- `lower_prediction_and_error` — local prediction, self-layer error,
  precision operation, and `c_self`;
- `upper_state_vjp` — transported upper contribution `c_upper` through the
  state VJP;
- `component_aggregation` — grouping technical pieces by canonical channel,
  summing channels, and computing geometry;
- `belief_update` — applying an already computed correction to belief state;
- `sweep_bookkeeping` — sweep/layer indices, version counters, convergence
  fields, and mandatory bookkeeping without adaptive decisions;
- `inference_finalize` — final consistency checks and return-object
  preparation before serialization.

No measured operation may belong to more than one region. Unattributed
residual time is retained and is not reassigned.

## Canonical layer-sweep event

Every `(model_seed, batch_id, sweep_index, layer_index)` stores:

```text
contract_id
source_git_commit
experiment_image
image_revision
torch_version
torch_hip_version
torch2pc_commit
checkpoint_sha256
config_sha256
split_manifest_sha256
input_sha256
target_sha256
model_seed
batch_id
sweep_index
layer_index
observer_mode
state_version_before
state_version_after
jacobian_version
canonical_channel_ids
c_self_norm
c_upper_norm
A
R
chi
Q
P
N
D
source_error_norm
transported_upper_norm
gamma
transport_status
observed_update_norm
reconstructed_update_norm
absolute_l2
relative_l2
max_abs
cosine
state_transition_absolute_l2
state_transition_relative_l2
state_transition_max_abs
state_transition_cosine
vjp_call_count
saved_tensor_count
saved_tensor_bytes
graph_birth_event
graph_release_event
synchronization_count
finite
passed
```

Non-applicable values are stored as `null`.

## Correction reconstruction

For every event, the implementation must export:

```text
u_observed
```

the tensor actually passed to the canonical update map before belief mutation.

The registered canonical channels independently form:

\[
u_l^{(\mathrm{reconstructed})}
  = c_l^{(\mathrm{self})} + c_l^{(\mathrm{upper})}.
\]

Technical pieces are first grouped by canonical channel id. They are not
treated as additional causal channels.

The primary barrier is:

\[
u_l^{(\mathrm{reconstructed})}
  \approx u_l^{(\mathrm{observed})}.
\]

The state transition is checked separately:

```text
h_after ≈ canonical_update_map(h_before, u_observed, eta)
```

The diagnostic path does not infer the update sign or scale. It calls the same
frozen update map used by canonical `Strict`.

## Numerical thresholds

The A1 implementation-snapshot profile is inherited for ROCm/float32:

```text
zero_atol = 1e-6
max_relative_l2 = 1e-3
max_abs = 1e-5
min_cosine = 0.999
```

Zero-safe rule:

1. if both norms are at most `zero_atol`, comparison uses `max_abs` and cosine
   is `null`;
2. if only one tensor is zero-like, the record fails;
3. NaN or infinity always fails the record.

CPU smoke uses A1 CPU/float64 thresholds and does not determine the
confirmatory decision.

## Sub-gates

### `REC-MA0` — reconstruction gate

It passes only if all 3600 confirmatory layer-sweep events are valid:

```text
10 model seeds * 3 batches * 20 sweeps * 6 layers = 3600
```

Requirements:

- the complete pair of canonical channels;
- `u_reconstructed ≈ u_observed`;
- state-transition equivalence;
- finite values;
- no duplicate event keys;
- no missing mandatory fields;
- correct zero-safe behavior.

Any failed reconstruction event fails `REC-MA0`.

Model-level `NCZ` and `ECZ` labels are not interpreted before `REC-MA0`
passes.

### `OBS-MA0` — non-interference gate

For each of 150 combinations:

```text
10 model seeds * 3 batches * 5 observer modes = 150
```

the following are compared with `no_hooks`:

- final belief states;
- loss;
- parameter gradients after state inference;
- model-state fingerprint;
- input/target fingerprint;
- post-run RNG fingerprint after allowed deterministic operations.

`instrumented_disabled`, `counters_only`, `tensor_summaries`, and
`full_attribution` must pass implementation-snapshot thresholds.

Each mode's overhead is published, but high overhead alone is not a numerical
failure.

### `VER-MA0` — state/Jacobian version gate

It passes only if:

- version fields are present for every event;
- `state_version_after = state_version_before + 1` at every belief update;
- state versions are monotone within each layer;
- the Jacobian version identifies the snapshot actually used;
- no channel record combines incompatible versions;
- snapshot fingerprints agree across reconstruction branches;
- sweep/layer order matches frozen `Strict`.

### `COST-MA0` — accounting gate

Primary device-time measurement uses:

```text
warmup_steps = 20
timing_repetitions = 5
measured_steps_per_repetition = 50
```

The same initial belief state is restored before every measured step.
Parameters are not updated.

ROCm events are recorded without per-region device synchronization. One
required synchronization is permitted at the end of each repetition to read
event durations. Every additional synchronization is recorded.

Every measured step stores:

- total `state_inference` device time;
- exclusive device time for each of the seven regions;
- wall time;
- synchronization count;
- VJP count;
- peak allocated/reserved memory;
- finite flag.

Expected raw counts for `counters_only`:

```text
total timing records:
10 * 3 * 5 * 50 = 7500

region timing records:
10 * 3 * 5 * 50 * 7 = 52500
```

Accounting residual:

\[
\rho =
\frac{
  \left|t_{\mathrm{total}}-\sum_r t_r\right|
}{
  \max(t_{\mathrm{total}}, 10^{-12})
}.
\]

`COST-MA0` passes if:

```text
rho <= 0.05
```

for at least 99% of measured steps and 100% of repetition-level aggregates,
all times are finite and nonnegative, and there are zero missing measured
steps.

Records with `rho > 0.05` are retained. The threshold is not changed after
data inspection.

### `CMP-MA0` — completeness and provenance gate

It passes only if:

- all 10 model seeds and three batch ids are present;
- all expected layer-sweep and timing records are present;
- all attempts are retained;
- checkpoint/config/input/target hashes verify;
- source commit and image digest are immutable;
- the test split was not accessed;
- dataset loading is outside the measured region;
- SHA256 manifests verify;
- the output contract JSON is byte-identical to the frozen implementation
  contract except for prespecified runtime provenance fields.

## Final gate

```text
si_ma0_passed =
    prerequisites_verified
    and REC-MA0
    and OBS-MA0
    and VER-MA0
    and COST-MA0
    and CMP-MA0
```

Decisions:

```text
pass:
  every sub-gate is true

fail:
  at least one scientific/contract sub-gate is false with complete evidence

inconclusive:
  evidence is incomplete for a documented infrastructure reason and no
  scientific failure is established
```

`inconclusive` does not authorize `NCZ`/`ECZ` interpretation or the next
stage.

## Primary estimands

### Mechanism validity

At event level:

- relative-L2 and max-absolute reconstruction error;
- relative-L2 and max-absolute state-transition error;
- proportion of passed events;
- counts of nonfinite, missing, and duplicate records.

This is an all-events gate, not a test of an average.

### Cost attribution

For model seed `m` and region `r`:

\[
s_{m,r}
=
\frac{\sum t_{m,r}}
     {\sum t_{m,\mathrm{state\_inference}}}.
\]

Summation first occurs across batch, repetition, and measured step within one
model.

Across models, publish:

- all ten `s_{m,r}` values;
- median;
- IQR;
- mean;
- 95% bootstrap confidence interval resampling only `model_seed`;
- fixed bootstrap seed `20260715`;
- `10000` bootstrap repeats.

No requirement is registered that a particular region must dominate. A null,
mixed, or seed-dependent result is published without replacing the estimand.

### Secondary diagnostics

Publish separately:

- observer-mode device/wall-time overhead;
- VJP counts by layer and sweep;
- saved-tensor count and bytes;
- graph lifetime in event-index units;
- synchronization count;
- correction-geometry and transport summaries;
- accounting-residual distribution;
- memory allocation summaries.

Secondary diagnostics do not redefine `si_ma0_passed`, except for explicitly
registered completeness, finite-value, and accounting checks.

## Multiplicity

`SI-MA0` registers no family of statistical null hypotheses. Primary validity
criteria are deterministic all-record gates.

Any later inferential comparison of mechanism features, diagnostic quotients,
predictor utility, or B1/B2 requires a separate preregistration and its own
multiplicity policy.

## Attempts and rerun policy

Every attempt receives an immutable `attempt_id`.

A repeat is permitted only after:

- retaining the failed attempt;
- classifying the cause as an infrastructure failure;
- preserving source commit, image, contract, seed, batch, and checkpoint;
- recording the replacement attempt's link to the original attempt.

Scientific failure, nonfinite tensors, reconstruction mismatch, high
accounting residual, or an inconvenient cost profile is not a reason to
delete or replace an attempt.

## Registered outputs

Working outputs:

```text
results/stage-3/si-ma0/working/
```

Future confirmatory evidence:

```text
results/stage-3/si-ma0/confirmatory/
```

Mandatory artifacts:

```text
si_ma0_contract.json
si_ma0_attempts.jsonl
si_ma0_environment.json
si_ma0_event_records.csv
si_ma0_mode_comparisons.csv
si_ma0_total_timing_records.csv
si_ma0_region_timing_records.csv
si_ma0_vjp_records.csv
si_ma0_saved_tensor_records.csv
si_ma0_graph_lifetime_records.csv
si_ma0_batch_summaries.csv
si_ma0_model_region_summaries.csv
si_ma0_summary.json
si_ma0_decision.json
SHA256SUMS
```

Raw tensors may be stored in NPZ outside Git, but their manifest and hashes
must be included in evidence.

## Interpretation boundary

When `si_ma0_passed=true`, the allowed claim is:

> On the registered final FashionMNIST `Strict` checkpoints, controlled ROCm
> lane, and fixed validation batches, the observed state-inference correction
> is reproduced by registered `PC-CATM` channels, observation is numerically
> non-interfering, versions are coherent, and call cost closes over
> prespecified regions within the accounting threshold.

The following claims are not allowed:

- the time shares are universal across models, batch sizes, devices, or
  checkpoints;
- `NCZ`, `ECZ`, or `TNZ` permits computation skipping;
- mechanism labels predict endpoint-gradient utility;
- reducing VJPs produces proportional speedup;
- a minimal sufficient quotient space has been found;
- active control is safe.

## Stage separation

This preregistration commit contains only:

```text
experiments/planned/STAGE3B-SI-MA0.md
experiments/planned/STAGE3B-SI-MA0_EN.md
experiments/planned/STAGE3B-SI-MA0-CONTRACT.json
```

Executable implementation, smoke, confirmatory execution, analysis, and
evidence are created in separate commits and branches.

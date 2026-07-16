# Stage 3B `SI-MA1` — observer-calibrated cost closure

[Русская версия](STAGE3B-SI-MA1.md)

## Status

This document and the machine-readable contract form the frozen
preregistration for step `A9`. The package must be sealed by the annotated tag
`stage3b-si-ma1-prereg-v1` before executable implementation and before the
first controlled smoke [execution](../../docs/glossary_EN.md#term-execution).

This package registers a new test. It does not replace `SI-MA0`, change its
threshold, or alter its retained result:

```text
REC-MA0  = pass
OBS-MA0  = pass
VER-MA0  = pass
COST-MA0 = fail
CMP-MA0  = pass
si_ma0_passed = false
```

Contract identifier:

```text
stage3b-si-ma1-v1
```

## Registered starting point

The following are fixed:

- base commit: `784459f7beade1980a12368283cf2dcb18642ad7`;
- `SI-MA0` [evidence](../../docs/glossary_EN.md#term-evidence) commit:
  `3db5eecaf4e7fb8f1de9a9d635465b95bb1bef93`;
- `SI-MA0` contract: `stage3b-si-ma0-v2`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

The new stage consumes the successful `REC-MA0`, `OBS-MA0`, `VER-MA0`, and
`CMP-MA0` sub-gates as prerequisites. The historical `COST-MA0=false`
decision remains unchanged.

## Research question

Is the un-attributed live [state inference](../../docs/glossary_EN.md#term-state-inference) timing gap explained
by a locally matched observer-cost calibration, such that the one-sided upper
95-percent confidence bound of the excess gap is no greater than one
percentage point?

## Three-arm block

For one [checkpoint](../../docs/glossary_EN.md#term-checkpoint), one data batch, and one restored initial state, three arms
are executed:

```text
A = baseline_no_observer
B = calibration_observer
C = live_attribution
```

- `A` uses `no_hooks`.
- `B` uses `counters_only` to estimate observer cost.
- `C` uses the same `counters_only` path and retains live region attribution.
- `B` and `C` must use the same callable, hooks, events, region boundaries,
  buffer writes, and synchronization policy.
- The `B` or `C` role label is assigned outside the [measured region](../../docs/glossary_EN.md#term-measured-region).
- Serialization occurs after the measured region.

Before each arm, the checkpoint, RNG snapshot, initial beliefs, inputs, and
targets are restored. This is a new [numerical-equivalence check](../../docs/glossary_EN.md#term-numerical-equivalence-check), not a
continuation of state from a previous arm.

## Balanced order

One three-arm block is repeated six times for every
`model_seed × validation_batch_id` pair.

All permutations are registered:

```text
ABC
BCA
CAB
ACB
CBA
BAC
```

The list is cyclically rotated by:

```text
(model_seed + validation_batch_id) mod 6
```

Each permutation occurs exactly once. Each arm occurs exactly twice in each
position. The order cannot change in response to intermediate results.

This is [matched profiling](../../docs/glossary_EN.md#term-matched-profiling),
not three isolated runs.

## Experimental scope

The registered [dataset](../../docs/glossary_EN.md#term-dataset) is `FashionMNIST`, and the registered [architecture](../../docs/glossary_EN.md#term-architecture) is `lenet_classic`.

```text
dataset = FashionMNIST
split = validation
architecture = lenet_classic
method = Strict
checkpoint = final
model_seeds = 0..9
validation_batch_ids = 0,1,2
batch_size = 256
dtype = float32
device = ROCm
eta = 0.05
inference_steps = 20
optimizer_step = disabled
parameter_update = disabled
test_split_access = false
```

The [independent statistical unit](../../docs/glossary_EN.md#term-statistical-unit) is the independently
trained model. The `model_seed` field identifies the [model seed](../../docs/glossary_EN.md#term-model-seed). Batch, order block, arm, and
measured step are nested observations.

## Timing protocol

For each `model_seed × validation_batch_id` pair:

1. each arm receives 20 unmeasured warmup steps;
2. the six registered blocks are executed;
3. each arm in each block contains 50 measured steps;
4. [device time](../../docs/glossary_EN.md#term-device-time) is measured with
   ROCm events;
5. synchronization occurs at the end of the arm block;
6. no per-region synchronization occurs;
7. dataset loading, checkpoint loading, and serialization remain outside the
   measured region.

One confirmatory [attempt](../../docs/glossary_EN.md#term-attempt) corresponds
to one `model_seed` and runs in an isolated process. Ten attempts are expected.

## Primary estimand

For one balanced block, the 50 measured steps are summed:

```text
A = total device time baseline_no_observer
B = total device time calibration_observer
C = total device time live_attribution
K = sum of seven exclusive live region times
```

All components are first compared in absolute device time:

```text
H = B - A
R = C - K
E = R - H = (C - K) - (B - A)
```

where:

- `H` is the signed observer cost;
- `R` is the signed un-attributed live gap;
- `E` is the residual after subtracting observer cost.

Normalization is performed once against the clean baseline time `A`:

```text
D = E / max(A, epsilon)
```

This avoids subtracting ratios with different denominators. Values of `H`,
`R`, `E`, and `D` are not truncated to zero. Absolute values are reported only
as secondary diagnostics.

For one model:

```text
D_seed = median(D over 3 batches and 6 order blocks)
```

Across the ten models, the primary statistic is the median `D_seed`.

The one-sided upper 95-percent bound is computed by percentile bootstrap:

```text
resampling unit = model_seed
bootstrap repeats = 10000
bootstrap seed = 20260716
```

The registered margin is:

```text
delta_excess = 0.01
```

`CAL-COST-MA1` passes if and only if:

```text
upper_95_bootstrap_bound(median(D_seed)) <= 0.01
```

Greater uncertainty increases the upper bound and therefore makes passing
harder.

The `delta_excess = 0.01` margin is one percent of clean baseline time `A`.
It is reserved only for residual SI-MA1 cost-closure error after locally
calibrating observer cost.

## `ECZ` evaluator boundary

SI-MA1 does not execute an `ECZ` evaluator. Its cost is not included in the
seven `K` regions, in `H`, or in the `delta_excess` margin.

Future B1/B2 stages must account for separate control-plane regions:

```text
diagnostic_feature_acquisition
ecz_evaluation
action_selection
fallback_validation
```

Those stages must compare the complete incremental cost of feature
acquisition, `ECZ` evaluation, action selection, and fallback validation with
the computation actually avoided. A positive SI-MA1 result does not establish
that an `ECZ` evaluator is cost-effective.

## Gates

### `NUM-MA1`

Passes when `A` versus `B` and `A` versus `C` preserve loss, final beliefs,
parameter gradients, model state, inputs, targets, and RNG within the
registered ROCm/float32 tolerances.

This gate checks [measurement non-perturbation](../../docs/glossary_EN.md#term-non-perturbation).

### `TOPO-MA1`

Passes when `B` and `C` have the same observer topology:

- hook count;
- event count;
- region-record count;
- saved-tensor policy;
- buffer-write count;
- synchronization count;
- `instrumentation-configuration hash`.

### `BAL-MA1`

Passes when every model and batch contains all six permutations exactly once
and every arm occupies every position twice.

### `CAL-COST-MA1`

Passes under the registered upper-confidence-bound rule. All times and block
estimands must be finite and complete, and all quantities required to be
nonnegative must be nonnegative.

### `CMP-MA1`

Passes with the complete matrix, retention of every
[run](../../docs/glossary_EN.md#term-run), verified checksums, and verified [artifact provenance](../../docs/glossary_EN.md#term-provenance). Test-split
access is forbidden.

## Final decision

```text
si_ma1_passed =
    prerequisites_verified
    and NUM-MA1
    and TOPO-MA1
    and BAL-MA1
    and CAL-COST-MA1
    and CMP-MA1
```

Decision states:

- `pass`: all registered gates are true;
- `fail`: evidence is complete and at least one gate is false;
- `inconclusive`: evidence is incomplete for a documented infrastructure
  reason and no scientific failure has been established.

This is a separate [decision gate](../../docs/glossary_EN.md#term-decision-gate). A positive result permits
only separate preregistration and implementation of `B1/B2`; it does not
authorize active compute control.

## Expected completeness

```text
confirmatory attempts = 10
model-seed/batch pairs = 30
matched blocks = 180
arm blocks = 540
arm timing records = 27000
live region timing records = 63000
numerical comparison rows = 360
topology comparison rows = 180
seed summaries = 10
order sensitivity rows = 6
```

## Secondary analysis

The following are published without authority to override the primary
decision:

- all `D_seed` values;
- mean and median summaries;
- two-sided bootstrap intervals;
- distributions of `O`, `G`, `D`, and their absolute values;
- order-, position-, and batch-stratified estimates;
- leave-one-order-out sensitivity;
- wall-time analogues.

## Rerun policy

Every [attempt](../../docs/glossary_EN.md#term-attempt) has an immutable
identifier and is retained. Replacement is allowed only for infrastructure
failure and requires identical source, image, contract, seed, batches, and
checkpoints. Scientific failure is not a replacement reason.

## Stage separation

The preregistration commit may modify only:

```text
docs/language-map.csv
experiments/planned/STAGE3B-SI-MA1.md
experiments/planned/STAGE3B-SI-MA1_EN.md
experiments/planned/STAGE3B-SI-MA1-CONTRACT.json
```

After merge, the annotated tag `stage3b-si-ma1-prereg-v1` is created.
Implementation, smoke execution, confirmatory execution, analysis, and [integrity sealing](../../docs/glossary_EN.md#term-integrity-sealing) use
separate commits.

## Interpretation boundary

If the decision is `pass`, the only authorized bounded statement is:

> In the registered scope, the un-attributed live timing gap does not exceed
> the independently matched observer-cost calibration by more than one
> percentage point at the one-sided upper 95-percent model-level bound.

The following remain unauthorized:

- changing the historical `COST-MA0=false` result;
- universal observer-cost claims;
- universal time-share claims;
- treating `delta_excess` as an `ECZ` evaluator runtime budget;
- claiming that SI-MA1 measures `ECZ` evaluator runtime;
- permission to skip computation;
- active-control safety;
- minimal sufficient quotient-space claims;
- proportional-speedup claims;
- transfer to another GPU, ROCm version, architecture, dataset, or observer
  topology.

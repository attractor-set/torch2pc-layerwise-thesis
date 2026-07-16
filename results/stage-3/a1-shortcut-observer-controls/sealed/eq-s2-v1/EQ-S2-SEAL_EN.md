# EQ-S2 evidence seal

## Status

EQ-S2 passed the confirmatory control in the canonical Docker CPU and Docker/ROCm execution lanes.

## Comparison

Reference:

- iterative FixedPred;
- `eta = 1`;
- `inference_steps = len(model) = 6`;
- feed-forward initialization.

Candidate:

- the opt-in reduced shortcut;
- one joint state-and-parameter VJP per top-level layer;
- `6` joint VJP calls;
- `6` detached graph islands;
- no `loss.backward()` in the candidate;
- no iterative FixedPred loop in the candidate.

## Evaluation scope

- experiment source commit: `35527137e94b99fd74891739b982ad3181385256`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- seeds: `0, 1, 2`;
- batches per seed: `10`;
- runs per lane: `30`;
- endpoint-gradient comparisons: `300/300` per lane;
- parameter-after-step comparisons: `300/300` per lane;
- total tensor comparisons: `1200/1200`.

## Supported claim

Under the registered lane-specific numerical thresholds, iterative FixedPred with `eta = 1` and `inference_steps = len(model)` reproduced endpoint gradients and parameters after one stateless SGD step relative to the joint-VJP reduced shortcut in the registered CPU and ROCm sample.

## Claim boundary

EQ-S2 does not establish equality of intermediate hidden-state trajectories, full training-trajectory equivalence, equivalence for stateful optimizers, runtime or memory benefit, observer non-interference, or universal equivalence outside the registered architecture and environment.

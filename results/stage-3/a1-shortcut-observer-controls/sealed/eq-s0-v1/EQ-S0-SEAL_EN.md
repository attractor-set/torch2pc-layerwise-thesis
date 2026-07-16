# EQ-S0 evidence seal

## Status

EQ-S0 passed the registered expanded control in the canonical Docker CPU and Docker/ROCm execution lanes.

## Registered scope

- source commit: `50d6e37183dec3e0719ad4a1f246d1b325d1b346`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- model seeds: `0, 1, 2`;
- batches per seed: `10`;
- runs per lane: `30`;
- endpoint-gradient comparisons: `300/300` per lane;
- parameter-after-step comparisons: `300/300` per lane;
- total tensor comparisons: `1200/1200`;
- observer mode: `no_hooks`;
- optimizer: `SGD(lr=0.001, momentum=0.0)`.

## Numerical thresholds

The control used a registered lane-specific threshold policy.

CPU:

- `min_cosine = 0.99999`;
- `max_relative_l2 = 1e-07`;
- `zero_atol = 1e-12`.

ROCm:

- `min_cosine = 0.999`;
- `max_relative_l2 = 0.001`;
- `zero_atol = 1e-07`.

CPU uses stricter numerical tolerances. Both policies were embedded in the experiment source before controlled execution.

Model seed remains the independent experimental unit. Batches are repeated control observations within a seed.

## Supported claim

Under the registered lane-specific thresholds, iterative FixedPred with `eta=1` and `n=len(model)` reproduced BP endpoint gradients and equivalent parameters after one stateless SGD step for the evaluated seeds and batches on CPU and ROCm lanes.

## Claim boundary

This gate does not establish intermediate hidden-state trajectory equivalence, full training-trajectory equivalence, equivalence for stateful optimizers, or reduced-shortcut equivalence. EQ-S1, EQ-S2, and observer non-interference remain open gates.

## Provenance

Full provenance, thresholds, environment metadata, and aggregate counts are recorded in `eq_s0_evidence_manifest.json`. File integrity is verified through `SHA256SUMS`.

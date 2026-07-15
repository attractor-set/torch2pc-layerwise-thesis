# EQ-S1 evidence seal

## Status

EQ-S1 passed the confirmatory control in the canonical Docker CPU and Docker/ROCm execution lanes.

## Implemented candidate

The reduced shortcut uses one joint state-and-parameter VJP for every top-level layer.

For `lenet_classic`:

- top-level layers: `6`;
- joint VJP calls per run: `6`;
- graph islands: `6`;
- parameterized layers: `5`;
- parameter components: `10`;
- candidate use of `loss.backward()`: none;
- iterative FixedPred loop use: none.

## Evaluation scope

- experiment source commit: `a2c634a066d871cf0dbf9c8e638dd830fe0e3705`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- seeds: `0, 1, 2`;
- batches per seed: `10`;
- runs per lane: `30`;
- endpoint-gradient comparisons: `300/300` per lane;
- parameter-after-step comparisons: `300/300` per lane;
- total tensor comparisons: `1200/1200`.

## Supported claim

Under the registered lane-specific numerical thresholds, the reduced shortcut using one joint VJP per layer reproduced BP endpoint gradients and parameters after one stateless SGD step in the registered CPU and ROCm sample.

## Claim boundary

EQ-S1 does not establish hidden-state trajectory equivalence, full training-trajectory equivalence, equivalence for stateful optimizers, runtime benefit, or equivalence with iterative FixedPred. The latter is evaluated separately in EQ-S2.

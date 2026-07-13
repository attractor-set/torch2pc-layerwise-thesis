# STAGE3-LAYERWISE-001: layer-wise gradient and representation diagnostics

[Русская версия](STAGE3-LAYERWISE-001.md)

## Status

Design-ready; the validation-only pilot is enabled after the patch is applied and unit tests pass.

## Baseline

- Stage 2 execution: `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2`;
- Stage 2 publication: `bb435432a65b76b7fc4f383b566b9a372fc346ae`;
- patched Torch2PC: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

## Questions

1. How do gradient cosine similarity, relative L2, and norm ratio vary with depth?
2. Do FixedPred and Strict deviations differ from the Exact–BP numerical control?
3. How similar are corresponding and cross-method layers under CKA/RSA?

## Pilot

- dataset: FashionMNIST;
- model: `lenet_classic`;
- model seeds: 0, 1, 2;
- five validation batches for the same-state probe;
- 1000 validation samples for the representation probe;
- best validation checkpoint;
- BP, Exact, FixedPred, and Strict;
- no test loader;
- no optimizer step;
- timing is measured in a separate execution path.

## Statistical unit

The independently trained model. Batches, parameters, and layers are repeated measurements within a model seed and are not independent replicas.

## Pilot freeze

Before the confirmatory run, freeze the layers, checkpoint schedule, probe sizes, Exact control thresholds, multiple-testing families, and degenerate CKA/RSA handling.

## Limitation

The first version operates on available checkpoints and final PC gradients. Intermediate training trajectories and per-inference-step traces require separate Stage 3 instrumentation changes.

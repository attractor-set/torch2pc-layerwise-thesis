# Research status

[Русская версия](STATUS.md)

Status after two completed 80-cell confirmatory campaigns. Stage 1 uses the
original Torch2PC implementation; Stage 2 uses the pinned
implementation-preserving patch. Numerical controls are scoped to the pinned
experimental domain and are not treated as a universal proof for arbitrary
models or environments.

| Component | Observed status |
|---|---|
| Validation-only pilot | 96/96 terminal cells, 0 failed, no test evaluation |
| Stage 1 final | 80/80 completed, 0 failed |
| Stage 2 final | 80/80 completed, 0 failed |
| Model and data | `lenet_classic`, MNIST, and FashionMNIST |
| Original Torch2PC | `00c6c50ee3540537bbb56ab2b6567b541f42b093` |
| Patched Torch2PC | `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |
| Stage 2 execution source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| CPU/GPU equivalence gates | Passed |
| Stage 1 / Stage 2 quality | Paired test accuracy and macro-F1 values matched |
| Stage 2 performance | Exact ≈ BP; FixedPred and Strict substantially faster |
| Cross-version analysis | Available in `results/cross-version/` |
| Torch2PC equivalence audit | `docs/torch2pc-patched-v1-equivalence.md` |
| Confirmatory results | Available for dissertation reporting |

## Current task

Post-experiment maintenance is complete: CSV checksums are stable, the Stage 2
manifest is bound to the correct environment lock, and the regression suite
contains 63 tests. The remaining work is to verify CI, create separate
execution/results-state tags, and publish the complete replication bundle with
raw run artifacts.

# Research status

[Русская версия](STATUS.md)

Stage 1 and Stage 2 are complete and remain an immutable published baseline. The
active work is preparation of an extended Stage 3 on locality, approximation,
and scaling.

| Component | Observed status |
|---|---|
| Validation-only pilot | 96/96 terminal cells, 0 failed, test not evaluated |
| Stage 1 final | 80/80 completed, 0 failed |
| Stage 2 final | 80/80 completed, 0 failed |
| Stage 1/2 model and data | `lenet_classic`, MNIST, and FashionMNIST |
| Original Torch2PC | `00c6c50ee3540537bbb56ab2b6567b541f42b093` |
| Patched Torch2PC | `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |
| Stage 2 execution source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Stage 2 results state | `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| Stage 2 CPU/GPU gates | passed |
| Regression suite after Stage 3 scaffold | 82 passed |
| Stage 1 / Stage 2 quality | paired test accuracy and macro F1 match |
| Stage 2 performance | `BP ≈ Exact < FixedPred << Strict` |
| Public release | completed on July 13, 2026 |
| Stage 3 design | `ready_for_stage3_implementation` |
| Stage 3 execution | blocked until candidates, gates, and freeze |

## Stage 3 readiness

The repository now contains the detailed protocol, two ADRs, the Stage 3 design
contract, profiling/pilot/final-template configurations, a locality trace and
profiling contract, a depth/width MLP family, deterministic plans for 288 profiling and 48
parameterized validation-only screening cells, and CLI/Make guards that keep Stage 3 outside
`TRAINING_STAGES`. The final template keeps `evaluation.use_test=false`.

```bash
make stage3-ready
make stage3-plan
```

## Next step

Implement a non-perturbing B0 profiling executor and produce the baseline
locality report. Then implement B1 isolated VJP and B2 composite VJP separately,
run CPU/GPU equivalence gates, and only then proceed to C1/C2. Stage 1/2 are not
rerun, and Stage 3 receives its own commits, environment lock, execution tag,
and publication state.

# Research status

[Русская версия](STATUS.md)

Stage 1/2 are complete immutable published baselines. Active work is Stage 3
design revision 2 on locality, exact execution, and predict-correct
approximations.

| Component | Observed status |
|---|---|
| Validation-only pilot | 96/96; test not evaluated |
| Stage 1 / Stage 2 | 80/80 and 80/80 |
| Original / patched Torch2PC | `00c6c50ee3540537bbb56ab2b6567b541f42b093` / `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |
| Stage 2 execution / publication | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` / `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| Stage 2 runtime | `BP ~= Exact < FixedPred << Strict` |
| Stage 3 design | `ready_for_stage3_implementation`, revision 2 |
| Stage 3 matrices | 336 profiling, 48 core pilot, 27 accelerator screening |
| Test access | disabled until a separate freeze |
| Stage 3 execution | blocked until candidate commits, gates, and locks |

## Predict-correct line

A0 is the FixedPred endpoint-equivalence control. C4 uses a layer-local EMA
initializer and exact correction; C5 uses a layer-scalar secant preconditioner
and exact correction. C3H/C6 remain deferred.

## Next step

Implement non-perturbing B0/A0 profiling, then B1/B2 and exact gates, then the
C1/C2 core pilot. C4/C5 receive a separate 27-cell validation-only screening
with residual and fallback guards. Stage 1/2 are not rerun.

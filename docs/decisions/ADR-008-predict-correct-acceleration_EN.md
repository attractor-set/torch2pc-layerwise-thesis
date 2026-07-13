# ADR-008: predict-correct acceleration as a separate Stage 3 track

[Русская версия](ADR-008-predict-correct-acceleration.md)

- Status: accepted for design revision 2;
- date: 2026-07-13;
- scope: Stage 3;
- changes Stage 1/2: no.

## Context

Stage 2 observed `BP ~= Exact < FixedPred << Strict`. A new track may therefore
use not only exact-VJP reorganization but also a fast numerical pattern: a cheap
local estimate moves beliefs closer to the solution and one or more exact
predictive-coding sweeps correct the estimate.

Torch2PC already computes VJPs without materializing a full Jacobian. Bit-level
approximations or runtime low-rank Jacobian construction are therefore not the
primary candidates because they do not remove the dominant repeated VJPs and
inference sweeps.

## Decision

Stage 3 adds a predict-correct line:

1. `fixedpred_finite_step_control`, an exact endpoint control with `eta=1` and
   steps equal to network depth;
2. `predict_correct_initialization`, a cheap layer-local initializer followed by
   `1/2/3/5` exact correction sweeps;
3. `local_secant_preconditioner`, a local scalar secant inverse-scale estimate
   followed by `1/2/3/5` exact correction sweeps;
4. deferred `hybrid_feedback_exact_refresh`;
5. deferred `layer_local_anderson`.

The main accelerator screening includes only the two approximation candidates
and Strict. Hybrid feedback and Anderson remain deferred until core Stage 3 is
complete.

## Methodological boundary

`fixedpred_finite_step_control` may receive only an endpoint-equivalence claim:
parameter gradients and one optimizer step are compared, while identical belief
trajectories are not required.

Predict-correct, secant, feedback, and Anderson are algorithm-changing. They use
non-inferiority, gradient-alignment, residual, performance, and fallback gates
and do not inherit a Stage 2 equivalence claim.

## Execution safeguards

Each predict-correct candidate requires at least one exact correction sweep,
Strict fallback on non-finite or increasing residuals, logging of VJPs,
correction sweeps, and fallback events, disabled test access until Stage 3
freeze, and separate Torch2PC candidate commits and environment locks.

## Consequences

A positive result estimates how much Strict computation can be replaced by a
cheap local estimate without a practically meaningful quality loss. A negative
result remains informative by showing that exact local correction or fresh
linearization is essential in the examined scope.

# Stage 3 protocol: locality, approximation, and predict-correct acceleration

[Русская версия](stage-3-protocol.md)

Status: **design-ready revision 2; [execution](glossary_EN.md#term-execution) blocked until candidates, numerical
gates, and a separate Stage 3 freeze exist**.

## 1. Purpose

Stage 3 is a new campaign and does not reopen Stage 1/2. It studies mathematical
locality, executed autograd structure, VJPs, memory, [runtime](glossary_EN.md#term-runtime), depth [scaling](glossary_EN.md#term-scaling), and
controlled approximations.

Three change classes are analyzed separately: implementation-preserving exact
[execution](glossary_EN.md#term-execution), exact shortcuts with [endpoint](glossary_EN.md#term-endpoint) equivalence, and algorithm-changing
approximations.

## 2. Immutable baseline

| Role | Identifier |
|---|---|
| Stage 2 [execution](glossary_EN.md#term-execution) source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Stage 2 [publication state](glossary_EN.md#term-publication-state) | `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| Stage 2 Torch2PC | `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |
| [Runtime](glossary_EN.md#term-runtime) order | `BP ~= Exact < FixedPred << Strict` |

[Execution](glossary_EN.md#term-execution) and publication remain distinct provenance points. Stage 1/2 are not
rerun.

## 3. Research questions

### RQ6. Locality profile

Measure dependency radius, graph span, VJP calls, synchronization points, and
saved tensor bytes.

### RQ7. Execution locality and throughput

Compare isolated layer-local graphs and composite VJPs under preserved math.

### RQ8. Adaptive budget

Assess adaptive stopping against inference steps, alignment, [runtime](glossary_EN.md#term-runtime), memory,
and validation quality.

### RQ9. Linearization frequency

Assess periodic/state-triggered VJP refresh between Strict and fixed
linearization.

### RQ10. Approximate feedback

Assess local approximate feedback with infrequent exact correction.

### RQ11. Predict-correct acceleration

Assess whether a cheap local belief or inverse-scale estimate followed by
`1–5` exact PC correction sweeps reduces VJPs and [runtime](glossary_EN.md#term-runtime) without a practically
meaningful quality loss.

## 4. Locality taxonomy

Publish algorithmic locality, dependency radius, graph locality, [execution](glossary_EN.md#term-execution)
locality, feedback locality, and orchestration locality separately. The
structural gate for mathematically local events is `dependency_radius <= 1`.

## 5. Candidates

### B0. `stage2_baseline`

Frozen Stage 2 patched Torch2PC.

### A0. `fixedpred_finite_step_control`

FixedPred with `eta=1` and steps equal to network depth. It uses [endpoint](glossary_EN.md#term-endpoint)
equivalence for parameter gradients and one optimizer step; belief-trajectory
equivalence is not claimed.

### B1. `isolated_layer_vjp`

Detached layer inputs and separate local graphs. Full-trajectory CPU/GPU gates
are required.

### B2. `composite_vjp`

Grouped exact local VJPs with the same full-trajectory gates.

### C1. `adaptive_stopping`

Residual-based stopping within fixed minimum and maximum steps.

### C2. `periodic_vjp_refresh`

Strict pullback refresh intervals `1, 2, 5, 20`.

### C3. `fixed_random_feedback`

Pure approximate feedback; deferred.

### C3H. `hybrid_feedback_exact_refresh`

Cheap feedback between exact VJP refreshes plus a required final exact
correction; deferred.

### C4. `predict_correct_initialization`

A layer-local EMA residual initializer followed by `1/2/3/5` exact correction
sweeps. Revision 2 fixes `ema_beta=0.9`, epoch reset, and Strict [fallback](glossary_EN.md#term-fallback) on
non-finite or increasing residuals.

### C5. `local_secant_preconditioner`

Two exact warmup sweeps, a layer-scalar secant scale clipped to `[0.25, 4.0]`,
and `1/2/3/5` exact correction sweeps. Strict [fallback](glossary_EN.md#term-fallback) is mandatory.

### C6. `layer_local_anderson`

Layer-local Anderson mixing with history window `2/3`; deferred.

## 6. Phases

### 6.1. Stage 3A — profiling

Profile `initial_forward`, `state_inference`, `local_state_vjp`,
`parameter_vjp`, and `optimizer_step`. Record time, VJPs, synchronization,
[saved tensors](glossary_EN.md#term-saved-tensors), memory, graph span, dependency radius, and actual steps. B0, A0,
B1, and B2 are included; A0 applies only to FixedPred.

### 6.2. Stage 3B — exact candidates

Run B1 gates, B2 gates, A0 [endpoint](glossary_EN.md#term-endpoint) gates, then randomized matched [profiling](glossary_EN.md#term-profiling).

### 6.3. Stage 3C — core approximations

Implement C1 and C2 and run the validation-only core pilot.

### 6.4. Stage 3C2 — predict-correct accelerator screening

After the core pilot, compare B0 Strict, C4, and C5. C3H/C6 remain deferred.
No test loader is created.

### 6.5. Stage 3D — scaling

Use depths `4/8/16/32`, widths `64/256`, batch sizes `64/256`, and seeds
`70/71/72`.

## 7. Matrices

### 7.1. Profiling

B0/B1/B2 contribute 288 short matched cells; A0 contributes 48 FixedPred-only
cells, for **336** total.

Each [experiment cell](glossary_EN.md#term-experiment-cell) uses 20 [warm-up](glossary_EN.md#term-warm-up) steps, 50 measured steps, 5 repetitions,
device synchronization, and hash-counterbalanced ordering.

### 7.2. Core validation-only pilot

B0/B1/B2: 18 cells; C1: 18; C2: 12; total **48**.

### 7.3. Predict-correct accelerator screening

B0 Strict: 3 cells; C4: 12; C5: 12; total **27** validation-only cells.

### 7.4. Final template

Test remains disabled until freeze. The final campaign contains at most 80
cells for one exact and one approximation [candidate](glossary_EN.md#term-candidate); a Strict-only
approximation yields 60 cells, and no passing approximation yields 40.

## 8. Gates

### 8.1. Full-trajectory equivalence

B1/B2 compare beliefs, prediction errors, state updates, parameter gradients,
and one optimizer step.

| Device | dtype | min cosine | max relative L2 |
|---|---|---:|---:|
| CPU | float64 | 0.99999 | `1e-7` |
| GPU | float32 | 0.999 | `1e-3` |

### 8.2. Endpoint equivalence

A0 compares parameter gradients and one optimizer step only.

### 8.3. Approximation/non-inferiority

C1–C6 report per-layer cosine, relative L2, sign agreement, residuals,
VJP/step reduction, validation macro F1, seed variance, and non-finite events.

### 8.4. Predict-correct guard

C4/C5 continue only with at least one exact correction, at least 25% mean VJP
reduction, at most 10% [fallback](glossary_EN.md#term-fallback), non-increasing residual after correction, no
new non-finite values, and validation [non-inferiority](glossary_EN.md#term-non-inferiority). [Fallback](glossary_EN.md#term-fallback) time and events
remain in the analysis.

### 8.5. Performance

Require at least 15% FixedPred or 20% Strict speedup, no more than 3% [baseline](glossary_EN.md#term-baseline)
regression, and no more than 15% memory growth without an ADR. These are
engineering continuation rules, not superiority claims.

## 9. Stop rules

Stop on insufficient Amdahl opportunity, failed exact gates, non-finite values,
increasing residuals, [fallback](glossary_EN.md#term-fallback) above 10%, or failed validation [non-inferiority](glossary_EN.md#term-non-inferiority).
Negative outcomes remain registered.

## 10. Test access and provenance

[Profiling](glossary_EN.md#term-profiling), both screenings, and the current final template keep test disabled.
Test is enabled only by a separate commit after `stage3-pilot-freeze-v1`.
Planned tags are `stage3-design-v1`, `stage3-pilot-freeze-v1`,
`stage3-execution-v1`, and `stage3-results-v1`; [execution](glossary_EN.md#term-execution) and publication
states remain distinct.

## 11. Twelve-month schedule

| Period | Deliverable |
|---|---|
| Months 1–2 | literature update, ADR/RQ freeze, [profiling](glossary_EN.md#term-profiling) executor |
| Months 3–4 | B0/A0 audit, locality traces, [scaling](glossary_EN.md#term-scaling) [baseline](glossary_EN.md#term-baseline) |
| Months 5–6 | B1/B2 and exact gates |
| Month 7 | C1/C2 and 48-cell core pilot |
| Month 8 | C4/C5 and 27-cell accelerator screening |
| Month 9 | freeze/core final; C3H/C6 go/no-go |
| Month 10 | robustness, representations, [scaling](glossary_EN.md#term-scaling) |
| Month 11 | thesis/article/replication bundle |
| Month 12 | clean-room reproduction and reserve |

## 12. Current readiness boundary

Repository readiness means ready to implement Stage 3A, not ready to run
pilot/final. [Candidate](glossary_EN.md#term-candidate) commits, environment locks, full-trajectory/[endpoint](glossary_EN.md#term-endpoint)
gates, [fallback](glossary_EN.md#term-fallback) tests, and a separate freeze are still required.

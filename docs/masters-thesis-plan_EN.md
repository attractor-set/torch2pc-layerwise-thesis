# Realistic master's thesis plan

[Русская версия](masters-thesis-plan.md)

## 1. Starting point

As of 15 July 2026, Stage 1, Stage 2, Stage 3A, the 96/96 Stage 3B B0 campaign,
its statistical/engineering analysis, and the bilingual terminology migration
are complete and published. B0 remains immutable; future work creates separate
controls, candidates, and [evidence](glossary_EN.md#term-evidence).

## 2. Primary scientific line

The thesis has three levels:

1. [PC-TREF](pc-tref-balanced-core_EN.md), the upper-level framework for
   task-relative diagnostic sufficiency;
2. [PC-CATM](pc-catm-operator-model_EN.md), the mechanism model of correction
   aggregation and error transport;
3. [Scenario A](stage3b-primary-scenario-a_EN.md), the single primary
   experimental path.

Central question:

> Can a cost-efficient diagnostic representation of `state_inference` retain
> enough information to safely choose the number of subsequent full exact
> sweeps?

## 3. Frozen mandatory scope

### Mandatory

Mandatory work includes shortcut/equivalence controls, observer
non-interference and overhead, deterministic NCZ/ECZ/TNZ controls, SI-MA0,
[candidate](glossary_EN.md#term-candidate)-specific B1/B2 gates, `EX-IF0`, passive PC-CATM diagnostics, nested
$\phi_0,\ldots,\phi_5$ ablations, [endpoint](glossary_EN.md#term-endpoint)-gradient utility, counterfactual
exact verification, shadow [QWake-PC](glossary_EN.md#term-qwake-pc), and active full-sweep QWake-PC only after
the safety gate passes.

### Limited extension

`PNZ` is limited to theory, one deterministic parameter-accessibility control,
and an optional small passive audit.

### Outside mandatory scope

Active kernel-preconditioned learning,
dual Gauss–Newton, layer-aware skipping, plasticity control, continual
learning, and universal TREF are outside mandatory scope.

## 4. Completion levels

### A-Min

Observer and deterministic controls pass, SI-MA0 reconstructs the observed
update, passive NCZ/ECZ/TNZ diagnostics are published, and PC-TREF
cost-sufficiency ablations are complete.

### A-Core

B1/B2 are evaluated, `EX-IF0` is frozen, the predictor is evaluated with
`model_seed` grouping, exact verification is complete, and QWake-PC passes
through shadow evaluation.

### A-Max

Active QWake-PC passes the dangerous-miss gate, reduces exact sweeps/VJPs and
[device time](glossary_EN.md#term-device-time), and preserves endpoint-gradient bounds. Failure to reach A-Max
does not invalidate A-Min or A-Core.

## 5. Work sequence

### July–August 2026

Freeze PC-TREF/PC-CATM/Scenario A, implement shortcut controls, validate
observer non-interference, and measure observer overhead.

### September–October 2026

Implement deterministic correction/transport controls, Rosenbaum temporal
control, the frozen [block-Jacobian probe](glossary_EN.md#term-block-jacobian-probe), and SI-MA0 reconstruction.

### November–December 2026

Evaluate B1/B2, compare time/memory/[saved tensors](glossary_EN.md#term-saved-tensors)/graph lifetime, and freeze
`EX-IF0` before predictor-label collection.

### January–February 2027

Collect passive PC-CATM observations, compare $\phi_0,\ldots,\phi_4$, construct
the empirical cost-sufficiency frontier, and prepare predictor data without
test access.

### March–April 2027

Train/evaluate the grouped-seed predictor, run counterfactual exact
verification, measure dangerous misses and regret, and complete shadow QWake-PC.

### May 2027

Conditionally run active full-sweep QWake-PC, freeze code/image/features/policy
and analysis, then open the final test split once.

### June 2027

Complete statistics, figures, bounded claims, reproducibility audit, thesis
consolidation, and defense materials.

## 6. Writing in parallel

Write background/methodology/Stage 1–3A by September 2026, B0 and PC-TREF/
PC-CATM theory by November, [mechanism attribution](glossary_EN.md#term-mechanism-attribution) by February 2027, diagnostic
sufficiency and shadow QWake by April, and discussion/conclusion in May–June.

## 7. Primary measurements

### Validity

Validity: endpoint-gradient cosine/relative L2, zero-safe absolute error,
optimizer-step parity, update reconstruction, and observer non-interference.

### Diagnostic sufficiency

Diagnostic sufficiency: dangerous misses, endpoint-gradient regret,
unnecessary wake-ups, [fallback](glossary_EN.md#term-fallback) rate, calibration, and generalization across
`model_seed`.

### Engineering measurements

Engineering: sweeps, VJPs, device/wall time, memory, saved tensors, graph
lifetime, synchronization, host transfer, and serialization cost.

## 8. Statistical contract

The independent unit is the separately trained model identified by
`model_seed`. Layer, sweep, batch, sample, and timing repetitions are nested.
Predictor splits are grouped by seed. Thresholds, features, and policy are
frozen before final test access.

## 9. Risk control

Shortcut failure does not block canonical Strict analysis. Composite-VJP
failure leaves B1 or canonical Strict. ECZ can remain descriptive if it lacks
incremental value. Predictor failure ends active control without invalidating
A-Min/A-Core. Sweep reduction without device-time benefit is retained as a
negative engineering result. Additional scope is accepted only after A-Core.

## 10. Contribution boundary

The intended contribution is PC-TREF-oriented and PC-CATM-grounded
`state_inference` diagnostics that test which mechanism distinctions are
necessary for safe allocation of full exact sweeps under controlled
endpoint-gradient regret.

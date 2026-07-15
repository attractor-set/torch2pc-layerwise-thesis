# Research questions and assumptions

[Русская версия](HYPOTHESES.md)

## Technical controls

C0 and C1 are implementation controls rather than superiority hypotheses. C0
compares observed Exact and BP gradients inside declared numerical tolerances.
C1 compares FixedPred at `eta=1` and sufficient iterations with Exact inside the
declared scope. A failed control blocks the corresponding experimental stage.

## RQ1. Classification quality

Paired macro-F1 differences between BP and selected PC regimes are assessed
against a predeclared practically meaningful margin. No direction is assumed.

## RQ2. Gradients

Layer-wise cosine similarity and relative L2 are assessed across regime, layer,
`eta`, and inference steps. Layer sensitivity may differ without a predefined
direction.

## RQ3. Representations

CKA/RSA representation similarity is compared with output similarity. Agreement
and divergence are both retained as possible observations.

## RQ4. Compute cost

Wall-clock time, memory, and run success are assessed under matched updates and
matched time budgets. No superiority direction is assumed.

## RQ5. Robustness

Quality change under noise, blur, and occlusion is assessed with corruption,
severity, seed, and metric fixed before final analysis.

## RQ6. Locality

Dependency radius, graph span, VJP calls, synchronization points, and saved
tensor bytes are assessed for FixedPred and Strict layer updates. Mathematical
locality and execution locality are separate dimensions.

## RQ7. Exact execution organization

Isolated layer-local graphs and composite VJP are compared while retaining the
update equations. The locality/runtime/memory trade-off has no predefined
direction.

## RQ8. Adaptive compute

Adaptive stopping is assessed through inference steps, gradient alignment,
runtime, memory, and validation quality.

## RQ9. Linearization refresh

Periodic VJP refresh is assessed as a family between Strict-like and
fixed-linearization regimes.

## RQ10. Approximate feedback

A conditional exploratory question evaluates a separate local feedback operator.
It has no Stage 2 equivalence claim and begins only after the core Stage 3 track.

## RQ11. Predict-correct acceleration

Assess whether a cheap layer-local belief or inverse-scale estimate followed by
one to five exact correction sweeps reduces VJPs and runtime under controlled
residual, fallback-rate, gradient-alignment, and validation non-inferiority
gates.


## Primary post-B0 Scenario A hypotheses

These hypotheses belong to a separate protocol/freeze and do not change
completed B0 findings.

- **H-CZ1:** activity, resultant efficiency, and destructive interaction add
  information about next exact-sweep utility beyond layer, sweep index, and
  residual norm.
- **H-T1:** transport diagnostics distinguish intrinsic NCZ from low observed
  contribution caused by attenuation or TNZ.
- **H-M1:** a validated `state_inference` decomposition explains measurable
  Strict/FixedPred differences in time, memory, and saved tensors.

- **H-TREF1:** correction geometry and state transport reduce operational
  manifestations of the task-relative equivalence defect relative to a
  residual-only representation.
- **H-TREF2:** among registered $\phi_0,\ldots,\phi_5$, one representation
  reaches a point where further features do not provide practically meaningful
  regret reduction relative to diagnostic cost.
- **H-Q1:** shadow QWake-PC reduces dangerous misses relative to residual-only
  or fixed-budget rules.
- **H-R1:** after observer cost is included, exact-sweep reduction yields device
  time reduction while endpoint gradients remain within registered bounds.

PNZ and the parameter tangent kernel are a limited exploratory extension and
are not part of the mandatory confirmatory hypothesis family.

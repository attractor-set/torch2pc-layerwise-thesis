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

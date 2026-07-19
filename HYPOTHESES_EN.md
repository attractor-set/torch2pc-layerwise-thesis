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
- **H-SB1:** a pre-action estimate of the oracle sufficiency margin adds
  out-of-sample information about unsafe next-sweep omission relative to
  registered magnitude-only baselines.
- **H-SB2:** temporal dynamics of the estimated margin and the first-order
  horizon add information beyond the current margin value.
- **H-SB3:** ECZ-protected non-cancelling activity reduces the false-safe rate
  relative to a resultant-direction-only feature.
- **H-R1:** after observer cost is included, exact-sweep reduction yields device
  time reduction while endpoint gradients remain within registered bounds.

PNZ and the parameter tangent kernel are a limited exploratory extension and
are not part of the mandatory confirmatory hypothesis family.

## Post-`SI-MA1` hypothesis refinement

This prospective refinement applies only to future B1/B2 preregistration. It
does not change the wording or results of completed Stage 1/2, B0, `SI-MA0`, or
`SI-MA1`. Normative semantics are defined by the
[`PC-TREF`/`PC-CATM` theoretical foundation](docs/pc-tref-pc-catm-theoretical-foundation_EN.md)
and [ADR-013](docs/decisions/ADR-013-pc-tref-operational-semantics_EN.md).

- **H-TREF1-OP:** registered diagnostic classes through $q_I$, or explicitly
  nontransitive operational indistinguishability, permit assessment of the
  task-relative equivalence defect through [decision regret](docs/glossary_EN.md#term-decision-regret),
  dangerous misses, or an equivalent prespecified outcome. No effect direction
  or magnitude is assumed.
- **H-TREF2-OP:** a nondominated representation may exist among preregistered
  representations under the [cost vector](docs/glossary_EN.md#term-cost-vector)
  and decision regret. This is not a global-minimality claim; the selection
  criterion, scalarization, or
  [Pareto admissibility](docs/glossary_EN.md#term-pareto-admissibility) is frozen
  before analysis.
- **H-R1-COST:** exact-sweep reduction counts as an end-to-end benefit only
  after separate accounting for [diagnostic-mechanism cost](docs/glossary_EN.md#term-diagnostic-mechanism-cost),
  [observer cost](docs/glossary_EN.md#term-observer-cost),
  [control-plane cost](docs/glossary_EN.md#term-control-plane-cost), and
  fallback. The negative `SI-MA1` residual is not used to offset future control
  cost.
- **H-B1:** a B1 candidate with an isolated layer-wise execution path may
  preserve registered numerical and safety bounds while improving at least one
  cost-vector component without degrading the others beyond prespecified
  tolerances.
- **H-B2:** a B2 candidate with a composite execution path may preserve the same
  bounds while producing a different locality/runtime/memory trade-off. No B1
  or B2 superiority direction is assumed.

These hypotheses permit only preparation of separate B1/B2 contracts.
Implementation and confirmatory execution remain closed until $q_I$ or the
proximity rule, $q_R$, the regret tolerance, norms, cost rule, fallback,
provenance, and candidate-specific decision gates are frozen.

### Operationalization of H-B1 and H-B2

H-B1 and H-B2 are linked to separate preregistered contracts,
`STAGE3B-B1-CONTRACT.json` and `STAGE3B-B2-CONTRACT.json`. Their numerical
component permits zero dangerous admissions, and their engineering component is
evaluated only after the full-trajectory gate. Effect direction and candidate
selection remain unresolved until execution, while `EX-IF0` remains a separate
decision. The contracts establish no estimator, oracle, hysteresis, or
`QWake-PC` policy.

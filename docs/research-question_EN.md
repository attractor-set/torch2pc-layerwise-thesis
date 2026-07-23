# Research question

[Русская версия](research-question.md)

## Observed problem

Torch2PC exposes several update rules, but matching final accuracy alone does
not explain where and why `Strict`, `FixedPred`, `Exact`, and BP differ in
layer-wise gradient geometry, representations, and cost. Stage 3A and B0 showed
that differences are layer-dependent and that `state_inference` is the dominant
engineering-cost region.

`SI-MA0` and `SI-MA1` further showed that mechanism-aware diagnostics are
measurable without a registered positive uncovered observer residual above 1%
after separate calibration. This justifies testing local exact candidates but
does not prejudge speedup or safety.

## Primary question

With [architecture](glossary_EN.md#term-architecture), data, initialization, and training budget fixed, how does
the update rule affect:

1. layer-wise gradient direction and scale;
2. representation similarity to BP;
3. computational cost and memory;
4. diagnostic sufficiency for selecting among `stop`, `local sweep`,
   `exact sweep`, and `fallback` under bounded
   [decision regret](glossary_EN.md#term-decision-regret)?

## Completed B1/B2 question and next bounded object

B1 `isolated_layer_vjp` and B2 `composite_vjp` tested exact alternatives to the
heavy path. Both candidates passed registered numerical equivalence, while
matched analysis preserved different cost vectors and `reject_or_revise`
decisions. The bounded supported conclusion is that numerical equivalence does
not guarantee resource equivalence. This conclusion does not prove that
adaptive control is necessary.

The next central question for the mandatory thesis path is:

> Can a frozen [QWake-FP](glossary_EN.md#term-qwake-fp) use a nested measurably
> cheap pre-action representation and a finite analytic registry to safely
> recognize a task-relative sufficient temporal FixedPred prefix before the
> full `stage2_baseline` suffix and retain positive end-to-end savings after
> complete observer, analytic, control, and [fallback](glossary_EN.md#term-fallback) cost?

Validation is bounded to the corrected Rosenbaum special case: `FixedPred`,
`eta=1`, a registered sequential architecture, and a finite canonical suffix.
It validates or falsifies only one concrete shadow implementation, not general
`QWake-PC` applicability.

The experimental logic is ordered:

1. do pre-terminal sufficient states exist;
2. are they recognizable from admissible pre-action data;
3. does frozen admission pass the safety gate;
4. do positive net savings remain?

The system compares acquiring the next observation level, running a registered
analytic step, executing the next canonical sweep, and `COMPLETE_SUFFIX`. `O`
is created only after action and is never a decision input.

All mandatory capabilities are implemented in one immutable superset image.
[Campaign roles](glossary_EN.md#term-campaign-role)
`C1_COLLECTION / C2_CALIBRATION / C3_CONFIRMATORY / R_REPLICATION` activate
them through internal [capability gates](glossary_EN.md#term-capability-gate)
without changing executable code between [evidence](glossary_EN.md#term-evidence) stages.

Recursive spatial aggregates, `Strict`, arbitrary `eta`, learned routing, and
active control remain future work rather than mandatory results.

## Theoretical framework

[PC-TREF](glossary_EN.md#term-pc-tref) bounds claims to a registered family of
diagnostics and decisions. An exact quotient requires a partition map;
[operational diagnostic indistinguishability](glossary_EN.md#term-operational-diagnostic-indistinguishability)
is threshold proximity without assumed transitivity.
[PC-CATM](glossary_EN.md#term-pc-catm) provides mechanism-aware correction and
transport features with explicit norm contracts and
[precision-masked zero](glossary_EN.md#term-precision-masked-zero).

## Research boundary

The study does not claim global representation minimality, universal predictive-
coding superiority, transfer to other architectures or devices, or active-
control safety before separate confirmatory experiments. The independent
statistical unit is the independently trained model identified by `model_seed`;
the test split remains closed until final freeze.

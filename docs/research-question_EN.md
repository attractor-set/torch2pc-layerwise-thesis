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

## Completed B1/B2 question and next direction

B1 `isolated_layer_vjp` and B2 `composite_vjp` tested exact alternatives to the
heavy path. Both candidates passed registered numerical equivalence, while
matched analysis preserved different cost vectors and `reject_or_revise`
decisions. The bounded supported conclusion is that numerical equivalence does
not guarantee resource equivalence. This conclusion does not prove that
adaptive control is necessary.

The next central question is:

> Can one recursive mechanism use an estimate of the margin to a task-relative
> sufficiency boundary to select
> [minimum sufficient compute aggregates](glossary_EN.md#term-minimum-sufficient-compute-aggregate)
> across multiple scales of predictive-coding inference under bounded
> exact-reference regret?

The work first tests existence of a cheaper sufficient aggregate, state
dependence of the oracle decision, and reuse of one normative semantics at two
scales. A predictor, temperature, and `QWake-PC` are admitted only after those
gates.

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

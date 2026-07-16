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

## Stage 3B question after `SI-MA1`

Can B1 `isolated_layer_vjp` and B2 `composite_vjp` replace part of the heavy
exact path while preserving registered numerical equivalence and safety, and
improve the [cost vector](glossary_EN.md#term-cost-vector) without moving hidden
cost into diagnostics, the observer, or the control plane?

The test separates three claims:

- **mechanism:** the [candidate](glossary_EN.md#term-candidate) reproduces the registered reference outcome;
- **decision:** candidate-selection errors remain within
  [required equivalence](glossary_EN.md#term-required-equivalence) and regret
  bounds;
- **cost:** savings persist after separate diagnostic-mechanism, observer,
  control-plane, and [fallback](glossary_EN.md#term-fallback) accounting.

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

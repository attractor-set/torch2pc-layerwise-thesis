# Research question

[Русская версия](research-question.md)

## Observed problem

Practical predictive-coding implementations differ in error equations, update
regimes, state-inference budgets, numerical precision, automatic-
differentiation organization, and computational cost. Final accuracy alone
does not describe layer-wise signals, [execution](glossary_EN.md#term-execution) locality, or the cost of
obtaining the result.

## Primary question

Under which pinned conditions do Torch2PC regimes remain close to BP in
quality, gradients, and representations, and under which conditions do their
differences exceed predefined bounds?

## Stage 3 extension

How do mathematical locality, graph and [execution](glossary_EN.md#term-execution) locality, [runtime](glossary_EN.md#term-runtime), memory,
and [scaling](glossary_EN.md#term-scaling) interact for FixedPred and Strict? Which exact computations can
be replaced by adaptive stopping or reused linearization while changes in
quality and gradient alignment remain controlled?

## Research boundary

Stages 1 and 2 apply to the pinned LeNet/MNIST/FashionMNIST conditions. Stage 3
adds a controlled multilayer-perceptron family for [scaling](glossary_EN.md#term-scaling) analysis. The
conclusions do not automatically extend to every predictive-coding algorithm,
hardware platform, or biological system.

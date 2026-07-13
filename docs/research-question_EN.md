# Research question

[Русская версия](research-question.md)

Practical predictive-coding implementations differ in error equations, update
mode, inference budget, numerical precision, autograd organization, and compute
cost. Final accuracy alone does not describe layer signals, execution locality,
or the cost of obtaining the result.

The primary question asks when pinned Torch2PC regimes remain close to BP in
quality, gradients, and representations, and when differences exceed declared
bounds. Stage 3 extends this question: how do mathematical locality, graph/
execution locality, runtime, memory, and scaling interact, and what exact work
can be replaced by adaptive stopping or reused linearization under controlled
quality and gradient-alignment changes?

Stage 1/2 conclusions remain limited to the pinned LeNet/MNIST/FashionMNIST
conditions. Stage 3 adds a controlled MLP scaling family. No automatic claim is
made for every predictive-coding algorithm, hardware backend, or biological
system.

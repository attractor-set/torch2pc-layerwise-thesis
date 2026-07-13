# Publication plan

[Русская версия](publication-plan.md)

The primary paired Stage 1/2 analysis is complete. The public narrative centers
on two separate observations:

1. Stage 1 and Stage 2 quality values matched pairwise in the pinned domain;
2. the implementation-preserving patch materially changed the runtime profile,
   after which the observed ordering was `BP ≈ Exact < FixedPred << Strict`.

Stage 2 execution source
`6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` is kept distinct from the
results/publication state
`bb435432a65b76b7fc4f383b566b9a372fc346ae`. Reproduction uses the
`stage2-execution-v1` and `stage2-results-v1` tags, with raw artifacts distributed
through the corresponding GitHub Release.

Public claims remain limited to `lenet_classic`, MNIST, FashionMNIST, seeds
0–9, the pinned commits, and the recorded Ubuntu/ROCm environment. Universal
equivalence, superiority, or novelty claims require separate empirical and
literature support.

Stage 3 is not required to publish the current results. New performance changes,
layer-wise diagnostics, robustness work, or transfer studies belong to a
separate campaign and do not rewrite Stage 1/2.

A later archival milestone may receive a semantic version and DOI after a
separate author decision and venue-policy review.

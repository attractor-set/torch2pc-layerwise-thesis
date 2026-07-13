# Research status

[Русская версия](STATUS.md)

Stage 1/2 are complete immutable published baselines. The **Stage 3A
layer-wise diagnostics** confirmatory subcampaign is complete; the broader
locality, profiling, and acceleration lines remain separate future work.

| Component | Observed status |
|---|---|
| Validation-only pilot | 96/96; test not evaluated |
| Stage 1 / Stage 2 | 80/80 and 80/80 |
| Stage 2 runtime | `BP ~= Exact < FixedPred << Strict` |
| Stage 3A same-state probes | 10/10 seeds |
| Stage 3A representation probes | 10/10 seeds |
| Exact–BP numerical controls | 10/10 passed |
| Gradient observations | 2250; cosine defined for 2250/2250 |
| Representation observations | 150; RSA defined for 150/150 |
| Cross-layer CKA observations | 750 |
| Regression suite | 94 passed |
| Stage 3A test access | validation-only diagnostics; no test loader created |
| Broader Stage 3 | profiling, locality, exact candidates, and approximations remain gated |

## Current interpretation

Stage 3A provides confirmatory layer-wise evidence for final FashionMNIST
`lenet_classic` checkpoints across seeds 0–9. The independently trained model
seed is the statistical unit; layers, batches, and samples are repeated
observations within a seed.

## Next step

Run paired seed-level statistics, Holm correction, effect-size estimation,
and figure generation. Continue locality/profiling and acceleration as
separate subcampaigns with their own provenance chains.

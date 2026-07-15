# Roadmap

[Русская версия](ROADMAP.md)

## Phases 1–5 — complete

Research scaffold, controlled environment and 96/96 validation-only pilot,
Stage 1 80/80, Stage 2 80/80, and the public release are complete.

## Phase 6 — Stage 3 design revision 2 complete

The locality/profiling contracts, exact candidates, core approximations, and
predict-correct candidates are specified.

## Phase 7 — Stage 3A layer-wise diagnostics complete

- same-state gradient probes for seeds 0–9;
- independently trained representation probes for seeds 0–9;
- Exact–BP controls passed for 10/10 seeds;
- aggregate gradient, CKA, RSA, and cross-layer evidence published;
- raw observations retained outside Git.

## Phase 8 — Stage 3A statistical publication complete

- the seed-level statistical unit is fixed;
- 40 gradient and 20 representation comparisons are complete;
- within-family Holm correction is applied;
- effect sizes, confidence intervals, and Exact controls are published;
- confirmatory depth analysis is complete;
- 8 PDF figures are published;
- metadata and SHA-256 manifests are present;
- a bilingual bounded findings report is published.

Publication tag: `stage3a-statistical-publication-v1`.

## Phase 9 — Stage 3B preregistration and B0 measurement baseline complete

- the profiling/locality preregistration and measurement contract are frozen;
- B0 candidate: `stage2_baseline` for `FixedPred` and `Strict`;
- the ROCm/float32 canonical campaign completed 96/96;
- every cell ran in a fresh Python child process;
- 0 failed attempts and 0 systemic resource failures;
- 96 cell, 480 region, 48 paired, and 32 configuration rows are published;
- validation, sealing, tag, and GitHub Release are complete;
- the test dataset was not accessed.

Publication tag: `stage3b-b0-evidence-v1`.

Evidence boundary: `full_b0_campaign_complete=true`,
`full_stage3b_campaign_complete=false`.

## Phase 10 — B0 statistical and engineering analysis complete

- the published sealed B0 evidence was analyzed without rerunning execution;
- `model_seed` is the independent unit, with 3 seeds per configuration;
- paired timing/memory effects, region attribution, saved tensors, and log2
  scaling summaries are published;
- median Strict/FixedPred device-time ratio: `2.327×`;
- median peak-allocated ratio: `1.328×`;
- dominant region: `state_inference`;
- state-inference saved-tensor ratio: `11.998×`;
- 8 derived tables, 4 PDF figures, a bilingual report, metadata, and
  `SHA256SUMS` are published;
- the decision gate permits candidate-specific B1/B2 equivalence work while
  keeping full matched profiling blocked.

Publication tag: `stage3b-b0-analysis-evidence-v1`.

## Phase 11 — B1/B2 candidate-specific numerical equivalence gates — next

- formalize B1 and B2 candidates relative to B0;
- implement candidates separately without modifying B0 evidence;
- pass cosine, relative-L2, finite-value, and stability gates;
- run a small profiling pilot only after equivalence acceptance;
- keep test access disabled;
- use a separate decision gate to authorize full matched B1/B2 profiling.

## Phase 12 — mechanism attribution and matched profiling

For accepted B1/B2 candidates, identify layer/module hotspots and
graph-retention costs before running the registered matched profiling matrix.
Structural locality claims require dedicated dependency-radius,
graph-span/lifetime, feedback-operator, and orchestration-barrier measurements.

## Phase 13 — core approximations and predict-correct

Run C1/C2 and C4/C5 as separate validation-only screening campaigns with
residual, fallback, non-inferiority, VJP-reduction, and stability gates.

## Phase 14 — extended Stage 3 freeze and final

Freeze selected candidates and parameters, preserve distinct execution and
publication states, and enable final test evaluation only after the freeze.

## Phase 15 — thesis and article

Integrate Stage 1/2, Stage 3A, and later profiling/locality/acceleration
results; publish replication bundles and complete clean-room reproduction.

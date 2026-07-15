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

## Phase 10 — B0 statistical and engineering analysis — next

In a separate `stage3b-b0-analysis-v1` branch:

- perform paired seed-level analysis of `Strict` relative to `FixedPred`;
- decompose time across profiling regions;
- analyze peak memory and saved-tensor attribution;
- analyze scaling across depth, width, and batch size;
- report bounded descriptive uncertainty with three model seeds per
  configuration;
- publish a bilingual report and a decision gate for later candidates.

## Phase 11 — exact execution and mechanism attribution

After the B0 analysis, run B1/B2 numerical gates, identify layer/module
hotspots, and only then freeze exact execution candidates.

## Phase 12 — core approximations and predict-correct

Run C1/C2 and C4/C5 as separate validation-only screening campaigns with
residual, fallback, non-inferiority, VJP-reduction, and stability gates.

## Phase 13 — extended Stage 3 freeze and final

Freeze selected candidates and parameters, preserve distinct execution and
publication states, and enable final test evaluation only after the freeze.

## Phase 14 — thesis and article

Integrate Stage 1/2, Stage 3A, and later profiling/locality/acceleration
results; publish replication bundles and complete clean-room reproduction.

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
- a bilingual bounded findings report is published;
- regression suite: 120 passed.

Publication tag: `stage3a-statistical-publication-v1`.

## Phase 9 — profiling/locality preregistration and measurement baseline — next

Create a separate `stage3b-profiling-locality-preregistration` branch and
freeze the following before a new campaign starts:

- validation-only scope and independent unit = model seed;
- B0/A0 profiling design;
- warm-up, device synchronization, and repetition rules;
- wall-clock, CPU/GPU time, peak memory, and VJP/backward attribution;
- locality taxonomy and B1/B2 gates;
- failure, exclusion, and missing-data rules;
- separation of exploratory attribution from confirmatory claims.

Profiling/locality does not modify the completed Stage 3A evidence and does not
make acceleration claims before measurement-validity gates pass.

## Phase 10 — exact execution and mechanism attribution

After profiling is validated, run B1/B2 numerical gates, identify layer/module
hotspots, and only then freeze exact execution candidates.

## Phase 11 — core approximations and predict-correct

Run C1/C2 and C4/C5 as separate validation-only screening campaigns with
residual, fallback, non-inferiority, VJP-reduction, and stability gates.

## Phase 12 — extended Stage 3 freeze and final

Freeze selected candidates and parameters, preserve distinct execution and
publication states, and enable final test evaluation only after the freeze.

## Phase 13 — thesis and article

Integrate Stage 1/2, Stage 3A, and later profiling/locality/acceleration
results; publish replication bundles and complete clean-room reproduction.

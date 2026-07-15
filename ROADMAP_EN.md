# Roadmap

[Русская версия](ROADMAP.md)

The roadmap separates completed stages from planned work. Progression requires
verified artifacts, preserved claim boundaries, and an explicit decision gate.

## Stages 1–5 — complete

1. Established the research scaffold and preregistration draft.
2. Pinned the controlled environment and completed the 96/96 validation-only
   pilot without accessing the test dataset.
3. Completed the Stage 1 confirmatory campaign, 80/80.
4. Completed the Stage 2 implementation study, 80/80.
5. Published the results and verified protection against unauthorized test
   access.

## Stage 6 — Stage 3 design revision complete

The locality and profiling contracts, exact candidates, core approximations,
and predict–correct candidates are specified.

## Stage 7 — Stage 3A layer-wise diagnostics complete

- same-state gradient probes completed for seeds 0–9;
- independently trained representation probes completed for seeds 0–9;
- Exact–BP numerical controls passed 10/10;
- aggregate gradient, CKA, RSA, and cross-layer CKA evidence published;
- raw observations retained outside Git.

## Stage 8 — Stage 3A statistical publication complete

- the independently trained model is the statistical unit;
- 40 gradient and 20 representation comparisons completed;
- within-family Holm correction applied;
- effect sizes, confidence intervals, and Exact controls published;
- confirmatory depth analysis completed;
- 8 PDF figures, metadata, and SHA-256 manifests published;
- a bilingual bounded-findings report published.

Publication tag: `stage3a-statistical-publication-v1`.

## Stage 9 — Stage 3B preregistration and B0 baseline complete

- profiling/locality preregistration and the measurement contract frozen;
- B0 candidate fixed as `stage2_baseline` for `FixedPred` and `Strict`;
- ROCm/float32 canonical campaign completed 96/96;
- every cell executed in a fresh Python child process;
- 0 failed attempts and 0 systemic resource failures recorded;
- 96 cell, 480 region, 48 paired, and 32 configuration rows published;
- validation, integrity sealing, tag, and GitHub Release completed;
- the test dataset was not accessed.

Publication tag: `stage3b-b0-evidence-v1`.

State boundary: `full_b0_campaign_complete=true`,
`full_stage3b_campaign_complete=false`.

## Stage 10 — B0 statistical and engineering analysis complete

- published sealed B0 evidence analyzed without rerunning execution;
- the independently trained model identified by `model_seed` is the unit, with
  three models per configuration;
- paired time and memory effects, measured-region attribution, saved-tensor
  analysis, and `log2` scaling summaries published;
- median Strict/FixedPred device-time ratio: `2.327×`;
- median peak-allocated-memory ratio: `1.328×`;
- dominant device-time region: state inference (`state_inference`);
- saved-tensor ratio within `state_inference`: `11.998×`;
- 8 derived tables, 4 PDF figures, a bilingual report, metadata, and
  `SHA256SUMS` published;
- the decision gate permits B1/B2 equivalence testing while keeping full
  matched profiling blocked.

Publication tag: `stage3b-b0-analysis-evidence-v1`.

## Phase 11 — primary Scenario A design freeze — complete

- remove the erroneous former ECZ meaning and reserve `Error-Cancellation Zone`;
- freeze PC-TREF Balanced Core and PC-CATM for canonical channels, NCZ/ECZ, and TNZ;
- adopt Scenario A as the single primary experimental path;
- retain PNZ and the parameter tangent kernel as a limited extension;
- leave B0 evidence unchanged and keep test access disabled.

## Phase 12 — shortcut, observer, and deterministic controls — next

- compare BP, iterative FixedPred with `eta=1`, `n=L`, and the reduced shortcut;
- verify observer non-interference before measuring overhead;
- run deterministic NCZ, ECZ, orthogonality, TNZ, and block-probe controls;
- use the Rosenbaum wavefront as an indexing and completion oracle.

## Phase 13 — SI-MA0, B1/B2, and EX-IF0

- decompose `state_inference` and verify reconstruction of the observed update;
- run candidate-specific B1 and B2 gates;
- compare device time, memory, saved tensors, and graph lifetime;
- select and freeze the exact implementation before predictor-label generation.

## Phase 14 — passive diagnostics and QWake-PC

- collect correction-geometry, transport, and temporal-persistence features;
- train and validate the local predictor with `model_seed`-grouped splits;
- run counterfactual exact verification of next-sweep utility;
- evaluate QWake-PC in shadow mode first;
- permit active control only at full-sweep granularity after safety and runtime gates.

## Phase 15 — extended Stage 3 freeze and final evaluation

Freeze the selected implementation, features, thresholds, predictor, fallback
rules, and statistical plan. Enable one final test evaluation only after this
freeze.

## Phase 16 — thesis and article

Integrate Stage 1/2, Stage 3A, B0, and Scenario A. Keep active parameter-kernel
learning, plasticity control, and layer-level skipping as future work or a
separate publication.

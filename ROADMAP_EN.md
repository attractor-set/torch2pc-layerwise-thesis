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

## Stage 11 — B1/B2 numerical-equivalence testing — next

- formalize B1 and B2 relative to B0;
- implement each candidate separately without modifying B0 evidence;
- apply registered cosine, relative-L2, finite-value, and stability criteria;
- run a small profiling pilot only after numerical-equivalence acceptance;
- keep test-dataset access disabled;
- use a separate decision gate to authorize the full matched B1/B2 profiling
  matrix.

## Stage 12 — mechanism attribution and matched profiling

For accepted B1/B2 candidates, identify layer and module hotspots, graph
retention cost, and measured-region contributions. Then run the registered
matched profiling matrix.

Structural-locality claims require dedicated measurements of dependency radius,
graph span and lifetime, the feedback operator, and orchestration barriers.

## Stage 13 — core approximations and predict–correct

Run C1/C2 and C4/C5 in separate validation-only screening campaigns. Evaluate
residuals, the exact fallback path, non-inferiority, VJP reduction, and
stability.

## Stage 14 — extended Stage 3 freeze and final evaluation

Freeze selected candidates and parameters, create distinct execution and
publication states, and enable final test evaluation only after the freeze.

## Stage 15 — thesis and article

Integrate Stage 1/2, Stage 3A, and later profiling, locality, and acceleration
results. Publish replication bundles and complete clean-room reproduction.

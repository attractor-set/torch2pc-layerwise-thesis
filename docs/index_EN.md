# Torch2PC Layer-wise Thesis documentation

[Русская версия](index.md)

This is the documentation portal for the completed `v1.0.0` dissertation.
Current public pages describe the post-T24 state. Historical plans,
[execution](glossary_EN.md#term-execution) requests, ADRs, and freeze records are
retained as research provenance and are not the current plan.

## Quick entry points

- [README](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/README_EN.md) — project overview and final outcomes;
- [STATUS](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/STATUS_EN.md) — authoritative current status and C01–C11 registry;
- [Research questions](research-question_EN.md) — RQ1–RQ3 and final answers;
- [Methodology](methodology_EN.md) — completed validation sequence;
- [Glossary](glossary_EN.md) — normative term meanings;
- [Repository validation](validation_EN.md) — current checks and `v1.0.0` release;
- [Roadmap](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/ROADMAP_EN.md) — follow-up research only;
- `thesis/main.tex` — canonical dissertation source;
- `thesis/data/thesis_traceability.json` — machine-readable C01–C11 traceability.

## Final research questions

| Question | Final status |
|---|---|
| RQ1 — behavior and internal mechanism | C01, C02 `supported` |
| RQ2 — cost and computational organization | C03–C06 `supported`; C07 `descriptive` |
| RQ3 — [QWake-FP](glossary_EN.md#term-qwake-fp) | C08 `supported`; C09 `rejected`; C10/C11 `not_tested` |

Stage 1/2 establishes the registered final-quality surface. Stage 3A separates
that result from gradient and representation similarity. Stage 3B B0 localizes
cost; B1/B2 pass numerical-equivalence checks, while subsequent
[matched profiling](glossary_EN.md#term-matched-profiling) does not open the
resource continuation criterion.

## QWake-FP

[QWake-FP](glossary_EN.md#term-qwake-fp) is the tested bounded implementation of
the general [QWake-PC](glossary_EN.md#term-qwake-pc). The registered early action
does not mean that all further computation disappears: the remaining canonical
iterative suffix is replaced by [analytic completion](glossary_EN.md#term-analytic-completion)
`fixedpred_eta1_wavefront_completion_v1`, while
`complete_suffix_stage2_baseline_v1` remains the exact reference and
[fallback](glossary_EN.md#term-fallback) path.

The best C2 rule is `compute_step >= 5`. It is a temporal fixed-prefix boundary,
does not demonstrate input-dependent adaptivity or superiority of PC-CATM features.
Registered 216/756 coverage contains 108 preterminal step-5 records and 108
terminal-boundary step-6 records. Zero observed dangerous accepts on this finite
calibration surface does not establish population-level safety.

C09 is rejected only under the frozen full decision-cost accounting. It does
not establish C10: marginal execution cost of a minimal recognizer was not
measured. C11 also remains `not_tested` because confirmatory C3 did not open in
the original protocol.

## Theoretical levels

- [PC-TREF](glossary_EN.md#term-pc-tref) — [task-relative equivalence](glossary_EN.md#term-task-relative-equivalence) and
  sufficiency framework;
- [PC-CATM](glossary_EN.md#term-pc-catm) — distinct linked mechanistic diagnostic
  level;
- QWake-PC — general research control [architecture](glossary_EN.md#term-architecture);
- QWake-FP — tested bounded special case.

PC-CATM motivates mechanism-aware features, but superiority of NCZ/ECZ/TNZ and
related transport/compensation features was not directly tested.

## Current and historical documents

Current entry surfaces are README, STATUS, ROADMAP, this index,
`research-question`, `methodology`, `validation`, project structure, and
subdirectory READMEs. Files named `analysis-plan`, `publication-plan`,
`masters-thesis-plan`, `stage-3-readiness`, `qwake-fp-experimental-plan`, ADRs,
old protocols, and execution requests are historical records and are not
rewritten to match final outcomes.

## `v1.0.0` release

`scripts/check_public_surface.py` validates the current public surface and
`scripts/check_release_contract.py` validates the release contract.
`scripts/build_release.sh` produces the source archive, final PDF, SHA-256
records, Git commit/tree metadata, and `release-manifest.json`. The GitHub
workflow for tag `v1.0.0` publishes those artifacts as a GitHub Release.

# Changelog

[Русская версия](CHANGELOG.md)

## [Unreleased] — B1/B2 preregistration

### Added

- separate paired documents and JSON contracts for B1/B2;
- a shared overview, ADR-014, and sequential B1 → B2 gate;
- zero dangerous admissions and a direct B1/B2 control;
- an explicit boundary to estimator, offline policy, hysteresis, and `QWake-PC`;

- a bilingual normative `PC-TREF`/`PC-CATM` foundation after `SI-MA1`;
- `ADR-013` covering operational diagnostic indistinguishability, regret-based
  required equivalence, precision-masked zero, explicit norm contracts, and
  separate cost boundaries;
- new glossary entries with identical `TERM-*` identifiers in both languages.

### Changed

- README, STATUS, ROADMAP, and the documentation index now reflect final
  `SI-MA1` and tag `stage3b-si-ma1-confirmatory-v1`;
- the research questions, hypotheses, analysis pre-specification,
  methodology, analysis plan, thesis plan, and Scenario A now define
  candidate-specific B1/B2 preregistration without retrospectively changing
  completed protocols;
- PC-TREF separates an exact partition-based quotient from nontransitive
  threshold proximity;
- PC-CATM requires explicit spaces, norms, scales, dtypes, thresholds, and
  aggregation rules;
- B1/B2 preregistration is permitted after publication, while implementation
  and execution remain closed pending separate contracts and gates.

### Preserved unchanged

- frozen B0, `SI-MA0`, and `SI-MA1` protocols and results;
- negative `COST-MA0` and final `CAL-COST-MA1=true`;
- raw/derived evidence, hashes, manifests, tags, and provenance;
- exclusion of future `ECZ` evaluator and control-plane cost from `SI-MA1`;
- `full_stage3b_campaign_complete=false` and the closed test split.

## [stage3b-b0-analysis-evidence-v1] — 2026-07-15

### Added

- deterministic B0 statistical and engineering analysis without rerunning
  execution;
- the independently trained model identified by `model_seed` as the
  statistical unit, with three models per configuration;
- 8 derived CSV tables, 4 PDF figures, a bilingual report, metadata, and
  `SHA256SUMS`;
- paired time and memory analysis, measured-region attribution, saved-tensor
  analysis, and descriptive `log2` scaling;
- GitHub tag and Release `stage3b-b0-analysis-evidence-v1`.

### Provenance

- analysis implementation: `e7a1632a947fae578e877826f0c923342669430e`;
- analysis publication state:
  `b9ff8b2ab76f8752b15dd3bb968565d05f1fe9d3`;
- execution source: `95c25d35224abd5e741f1df9327662ff2fde23ad`;
- integrity-sealing source: `caa226cc1cd5d4aa0f9772c1fb997f7388d60730`;
- sealed-bundle digest:
  `6a3d61838810e559a39f13e6ac39d6b22624c21d72523bddb55c33e83063c93e`.

### Bounded findings

- median Strict/FixedPred device-time ratio: `2.327×`, with a configuration
  range of `1.966–2.619×`;
- median peak-allocated-memory ratio: `1.328×`;
- dominant device-time region: state inference (`state_inference`);
- saved-tensor ratio within `state_inference`: `11.998×`.

### Decision gate and claim boundary

- candidate-specific B1/B2 equivalence testing is permitted;
- full matched B1/B2 profiling remains blocked until candidate-specific checks
  pass;
- structural-locality claims remain blocked pending dedicated structural
  measurements;
- new B0 execution is not required;
- the test dataset was not accessed;
- the full Stage 3B program remains incomplete.

## [stage3b-b0-evidence-v1] — 2026-07-15

### Added

- Stage 3B B0 ROCm/float32 canonical campaign: 96/96 cells, 0 failed;
- a fresh Python child process per cell: 96 records and 96 unique PIDs;
- compact derived evidence: 96 cell, 480 region, 48 paired, and 32
  configuration rows;
- metric definitions, validation, content-addressed integrity sealing, and
  `SHA256SUMS`;
- Git-stable LF serialization for evidence CSV files;
- GitHub tag and Release `stage3b-b0-evidence-v1`.

### Provenance

- execution source: `95c25d35224abd5e741f1df9327662ff2fde23ad`;
- integrity-sealing source: `caa226cc1cd5d4aa0f9772c1fb997f7388d60730`;
- publication state: `ed0d48063a17e2d9c6679869a4d930f933877052`;
- archive inventory checksum:
  `9abc6434b0f59b510e14ef0ad09d5c3b92a4a9472a90974cb92cdb1657e232ed`;
- sealed-bundle digest:
  `6a3d61838810e559a39f13e6ac39d6b22624c21d72523bddb55c33e83063c93e`.

### Claim boundary

- the B0 measurement baseline is complete and publication-permitted;
- the test dataset was not accessed;
- the full Stage 3B program remains incomplete;
- comparative time, memory, and scaling findings are reserved for the
  separate B0 analysis.

## [stage3a-statistical-publication-v1] — Stage 3A statistical publication

### Added

- final bilingual report `docs/stage3a-statistical-results*.md`;
- seed-level confirmatory statistics: 40 gradient and 20 representation
  comparisons;
- confirmatory depth analysis: 180 seed-level and 24 statistical rows;
- 8 publication PDF figures, provenance metadata, and a separate figure
  `SHA256SUMS` manifest;
- public links to statistics, figures, metadata, and SHA-256 manifests;
- the Stage 3 profiling and locality foundation: taxonomy, measurement
  contract, structural checks, and acceleration candidates;
- deterministic Stage 3 plan: 336 profiling cells, 48 core validation-only
  pilot cells, and 27 predict–correct screening cells.

### Changed

- marked Stage 8 complete;
- synchronized README, STATUS, and ROADMAP with the published Stage 3A
  statistics, depth analysis, and figures;
- bounded conclusions to FashionMNIST, `lenet_classic`, seeds 0–9, the pinned
  implementation, and the validation-only protocol.

### Preserved unchanged

- published Stage 3A evidence was not regenerated;
- Stage 1/2 execution and publication states were unchanged;
- immutable evidence history and existing tags were not moved.

## [stage2-results-v1] — 2026-07-13

### Added

- Stage 2 completed 80/80 with patched Torch2PC
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- Stage 2 execution source
  `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2`;
- results publication state
  `bb435432a65b76b7fc4f383b566b9a372fc346ae`;
- scoped CPU/GPU numerical checks for original and patched implementations;
- cross-version paired records and summaries;
- implementation-equivalence audit for `torch2pc-patched-v1`;
- release tooling and 63 regression tests;
- replication bundle with raw Stage 2 artifacts, archive SHA-256, and a file
  manifest;
- verification of 660 manifest artifacts.

### Observed

- paired Stage 1/2 test accuracy and macro-F1 matched;
- BP runtime was effectively unchanged;
- Exact approached BP runtime and was approximately 14% faster than Stage 1;
- FixedPred was approximately 31% faster;
- Strict was approximately 26% faster;
- Stage 2 runtime ordering was `BP ≈ Exact < FixedPred << Strict`.

## [stage2-execution-v1]

The execution tag identifies the Stage 2 code separately from the later
results publication state. The Stage 1 protocol was retained; the pinned
Torch2PC implementation was the controlled intervention.

## [confirmatory-final-v1]

- Stage 1 completed 80/80, with 0 failed runs;
- original Torch2PC:
  `00c6c50ee3540537bbb56ab2b6567b541f42b093`;
- project source state:
  `140e77cc2083bf04234dcea16b95803e63cb0537`;
- preceding pilot: 96/96 without test evaluation;
- selected parameters: FixedPred `eta=0.1`, `n=10`; Strict `eta=0.05`, `n=20`.

## [0.1.0] — first commit

Added the neutral research stance, preregistration draft, test isolation,
pilot-freeze gate, append-only run registry, persistent split checksums,
Ubuntu/ROCm container scaffold, statistical utilities, static checks, and the
initial dissertation and article structure. This entry describes the project
before empirical results were obtained.

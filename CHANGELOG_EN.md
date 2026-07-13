# Changelog

[Русская версия](CHANGELOG.md)

## [Unreleased] — Stage 3A statistical publication

### Added

- The final bilingual `docs/stage3a-statistical-results*.md` report.
- Seed-level confirmatory statistics: 40 gradient and 20 representation
  comparisons.
- Confirmatory depth analysis: 180 seed-level and 24 statistical rows.
- Eight publication PDF figures, provenance metadata, and a separate figures
  `SHA256SUMS` manifest.
- Public links to statistics, figures, metadata, and SHA-256 manifests.
- The Stage 3 profiling/locality design foundation: locality taxonomy,
  profiling contract, structural gates, and exact/approximation/predict-correct
  candidates.
- A deterministic Stage 3 design plan with 336 profiling cells, 48
  parameterized core validation-only pilot cells, and 27 predict-correct
  screening cells.

### Changed

- Marked Phase 8 complete.
- Synchronized README, STATUS, and ROADMAP with the published Stage 3A
  statistics, depth, and figure evidence.
- Updated the regression-suite count to the current 120 passing tests.
- Defined the next stage as the separate
  `stage3b-profiling-locality-preregistration` branch.
- Explicitly bounded conclusions to FashionMNIST, `lenet_classic`, seeds 0–9,
  the pinned implementation, and the validation-only protocol.

### Preserved unchanged

- Committed Stage 3A evidence was not regenerated.
- Stage 1/2 execution and publication states were not changed.
- Immutable evidence history and existing tags were not moved.

## [stage2-results-v1] — 2026-07-13

### Added

- Stage 2: 80/80 completed with patched Torch2PC
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.
- Stage 2 execution source
  `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2`.
- Results/publication state
  `bb435432a65b76b7fc4f383b566b9a372fc346ae`.
- Scoped CPU/GPU original-vs-patched numerical gates.
- Cross-version pair records and summaries.
- The `torch2pc-patched-v1` implementation-equivalence audit.
- Release tooling and regression coverage totaling 63 passing tests.
- A replication bundle containing raw Stage 2 artifacts, archive SHA-256, and a
  file manifest.
- Verification of 660 manifest artifacts.

### Observed

- Paired Stage 1/2 test accuracy and macro-F1 values matched.
- BP runtime was effectively unchanged.
- Exact approached BP runtime and was approximately 14% faster than Stage 1.
- FixedPred was approximately 31% faster.
- Strict was approximately 26% faster.
- Stage 2 runtime ordering was `BP ≈ Exact < FixedPred << Strict`.

## [stage2-execution-v1]

The execution tag identifies the code used for Stage 2 separately from the
later results state. The Stage 1 experimental protocol was retained, and the
pinned Torch2PC implementation was the controlled intervention.

## [confirmatory-final-v1]

- Stage 1: 80/80 completed, 0 failed.
- Original Torch2PC:
  `00c6c50ee3540537bbb56ab2b6567b541f42b093`.
- Source lock: `140e77cc2083bf04234dcea16b95803e63cb0537`.
- Preceding validation-only pilot: 96/96, without test evaluation.
- Selected parameters: FixedPred `eta=0.1`, `n=10`; Strict `eta=0.05`,
  `n=20`.

## [0.1.0] — First commit

Added the neutral research stance, preregistration draft, test isolation,
pilot-freeze gate, append-only registry, persistent split checksums,
Ubuntu/ROCm container scaffold, statistical utilities, static checks, and the
initial dissertation/article structure. This entry describes the scaffold
before empirical results were obtained.

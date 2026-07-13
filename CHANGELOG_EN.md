# Changelog

[Русская версия](CHANGELOG.md)

## [Unreleased] - Validation pilot milestone

- Pinned Torch2PC and the controlled ROCm environment.
- Recorded CPU/GPU C0 and C1 artifacts.
- Completed all 96 validation-only pilot cells without test evaluation.
- Recorded the selected FixedPred and Strict parameters.
- Added compact `pilot_observations.csv` export and provenance validation.
- Added pilot selection, candidate summary, observations, and registry hashes to
  the `pilot-freeze` manifest.

Final remains blocked until the selected environment is re-locked, the short
controls are repeated, and `pilot-freeze` is created.

## [0.1.0] - First commit

Added a neutral research protocol, pre-specification, test isolation, pilot
freeze gate, immutable run attempts, persistent split checksums, strict
reproducibility settings, pilot grids, statistical utilities, controlled
Ubuntu/ROCm scaffolding, and static tests. No empirical result is claimed.

Additional first-commit safeguards include an immutable source-revision image
label, environment lock, per-sample prediction artifacts, pilot-matrix
completeness checks, duplicate final-run prevention, paired confirmatory
reporting, and an explicit threats-to-validity document.

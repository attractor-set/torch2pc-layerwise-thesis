# Results and evidence

[Русская версия](README.md)

`results/` contains the public tracked result surface: aggregates, tables,
figures, compact manifests/evidence packages, and frozen analysis outputs. Raw
local runs, checkpoints, and separate forensic artifacts do not automatically
become part of the Git release.

The final dissertation consumes results only through validated thesis-facing
bindings. C01–C11 statuses are defined by `thesis/data/research_claims.json`;
provenance/section binding is checked through
`thesis/data/thesis_traceability.json` and `scripts/build_thesis_assets.py`.

Main areas:

- Stage 1: `summaries/`, `tables/`, `figures/`;
- Stage 2: `stage-2/` and cross-version comparison;
- Stage 3A: layer-wise gradient/representation outputs;
- Stage 3B: B0, SI-MA0/SI-MA1, B1/B2, matched profiling and analysis;
- QWake: bounded scientific summaries and frozen identifiers consumed by the
  dissertation contract.

A file in this directory does not by itself change a claim status.
`supported/rejected/descriptive/not_tested` comes only from the registered
decision contract and final thesis reconciliation.

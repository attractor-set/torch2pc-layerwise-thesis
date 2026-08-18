# Notebooks

[Русская версия](README.md)

`analysis/` contains analysis-only notebooks for registered artifacts. They
must not modify experimental configurations, perform hidden hyperparameter
selection, or define a new scientific claim.

`legacy/full_pipeline_v11.ipynb` is a historical migration baseline retained
for regression/provenance purposes. It is not the `v1.0.0` orchestration layer.

Canonical executable logic lives in `src/torch2pc_thesis/`; final numerical
claims are validated separately through the thesis-facing contracts.

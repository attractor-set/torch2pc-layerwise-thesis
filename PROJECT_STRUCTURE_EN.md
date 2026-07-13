# Repository structure

[Русская версия](PROJECT_STRUCTURE.md)

The repository separates scientific implementation, configuration,
experiment lifecycle, analysis, dissertation text, and publication artifacts.

The main rule is:

```text
Issue
-> ADR for protocol changes
-> test
-> src module
-> YAML configuration
-> CLI
-> documentation
-> validation-only experiment
-> freeze
-> final experiment
-> aggregate result
-> dissertation section
```

`src/` is the canonical source of scientific logic. Analysis notebooks consume
registered results and do not contain unique training or metric implementations.
English user-facing documents use the `_EN` suffix.

`RESEARCH_PRINCIPLES.md`, `HYPOTHESES.md`, and `PREREGISTRATION.md` define
the epistemic position, research questions, and confirmatory boundaries before
final test access.

The `requirements/` directory separates the CPU development wheel index from
the ROCm container lock. Dataset assets and their hashes are bound to
`environment-lock.json` through `src/torch2pc_thesis/assets.py`.


Raw runs and checkpoints are not stored in the `main` Git tree. The complete
Stage 2 raw artifact set is distributed through the `stage2-results-v1`
replication bundle.


## Stage 3 additions

Stage 3 adds `configs/stage3/design.yaml`, profiling/pilot/final templates,
candidate overlays, `src/torch2pc_thesis/locality.py`,
`src/torch2pc_thesis/profiling.py`, and `src/torch2pc_thesis/stage3.py`.
The new modules define the locality trace schema, measured profiling regions,
deterministic design plans, and readiness guards. Stage 3 remains outside
`TRAINING_STAGES` until candidate commits, numerical gates, environment locks,
and freeze artifacts exist.

Stage 1/2 evidence, tags, and published manifests remain immutable. Stage 3 uses
its own registry, results tree, execution commit, and publication state.

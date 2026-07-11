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
-> experiment
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

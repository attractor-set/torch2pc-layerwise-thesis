# Configuration system

[Русская версия](README.md)

Configurations preserve historical Stage 1/2/3 execution surfaces and hardware
profiles. Later values in the resolution chain override earlier ones, and each
registered run stores the fully resolved configuration with its SHA-256.

```text
base.yaml
-> hardware/<profile>.yaml
-> stages/<stage>.yaml
-> methods/<method>.yaml
-> experiments/<optional-experiment>.yaml
-> CLI overrides
```

## Stage 3 design contract

`configs/stage3/design.yaml` preserves baseline hashes, candidates, phases,
gates, stop rules, and planned provenance from the historical Stage 3 program.
Stage templates and B0/B1/B2 overlays remain for reproducibility and are not
new authorization for execution after `v1.0.0`.

Terminology boundary: older `C1/C2/C3` labels in the Stage-3 configuration
design predate the final QWake claim chain. Read them in the context of their
specific configuration/protocol file; do not automatically equate them with
QWake C1/C2/C3 or dissertation claims C01–C11.

Current scientific statuses are defined by `thesis/data/research_claims.json`,
not by a stage-template state.

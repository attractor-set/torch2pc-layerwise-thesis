# Configuration system

[Русская версия](README.md)

The primary configuration is merged in this order:

```text
base.yaml
-> hardware/<profile>.yaml
-> stages/<stage>.yaml
-> methods/<method>.yaml
-> experiments/<optional-experiment>.yaml
-> CLI overrides
```

Later values override earlier values. Every run stores the fully resolved
configuration and its SHA-256.

## Stage 3

`configs/stage3/design.yaml` is a separate design contract containing baseline
hashes, candidates, phases, gates, stop rules, and planned provenance. Stage
templates are `stage3_profiling.yaml`, `stage3_pilot.yaml`, and
`stage3_final_template.yaml`. B0/B1/B2 overlays describe baseline and exact
implementation candidates; C1/C2/C3 describe approximations. These stages are
not in `TRAINING_STAGES`, preventing accidental execution.

```bash
PYTHONPATH=src python -m torch2pc_thesis.cli stage3-check
PYTHONPATH=src python -m torch2pc_thesis.cli stage3-plan \
  --output build/stage3/stage3_design_plan.json
```

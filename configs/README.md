# Система конфигураций

[English version](README_EN.md)

Основная конфигурация собирается последовательно:

```text
base.yaml
-> hardware/<profile>.yaml
-> stages/<stage>.yaml
-> methods/<method>.yaml
-> experiments/<optional-experiment>.yaml
-> переопределения CLI
```

Более поздние значения переопределяют более ранние. Каждый запуск сохраняет
полностью разрешённую конфигурацию и её SHA-256.

## Stage 3

`configs/stage3/design.yaml` является отдельным design contract. Он фиксирует
baseline hashes, candidates, phases, gates, stop rules и planned provenance.

Stage 3 stage templates:

- `stage3_profiling.yaml`;
- `stage3_pilot.yaml`;
- `stage3_final_template.yaml`.

Candidate overlays используют префиксы B0/B1/B2 для baseline и точных
implementation candidates, C1/C2/C3 — для аппроксимаций. Эти stage names не
входят в `TRAINING_STAGES`, поэтому их нельзя случайно запустить через CLI.

Проверка:

```bash
PYTHONPATH=src python -m torch2pc_thesis.cli stage3-check
PYTHONPATH=src python -m torch2pc_thesis.cli stage3-plan \
  --output build/stage3/stage3_design_plan.json
```

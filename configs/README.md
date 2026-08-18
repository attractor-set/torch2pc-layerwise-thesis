# Система конфигураций

[English version](README_EN.md)

Конфигурации фиксируют исторические Stage 1/2/3 execution surfaces и аппаратные
профили. Более позднее значение в цепочке разрешения переопределяет более раннее,
а каждый зарегистрированный запуск сохраняет полностью resolved configuration и
её SHA-256.

```text
base.yaml
-> hardware/<profile>.yaml
-> stages/<stage>.yaml
-> methods/<method>.yaml
-> experiments/<optional-experiment>.yaml
-> CLI overrides
```

## Stage 3 design contract

`configs/stage3/design.yaml` хранит baseline hashes, candidates, phases, gates,
stop rules и planned provenance исторической Stage 3 программы. Stage templates
и B0/B1/B2 overlays сохраняются для воспроизводимости и не являются новым
разрешением на выполнение после `v1.0.0`.

Важно для терминологической дисциплины: старые обозначения `C1/C2/C3` в
Stage-3 configuration design предшествуют финальной QWake claim chain. Их нужно
читать в контексте конкретного configuration/protocol файла, а не автоматически
отождествлять с QWake C1/C2/C3 или диссертационными C01–C11.

Текущие научные статусы определяются `thesis/data/research_claims.json`, а не
состоянием stage template.

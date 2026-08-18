# Результаты и доказательные материалы

[English version](README_EN.md)

`results/` содержит публичную отслеживаемую поверхность результатов: агрегаты,
таблицы, рисунки, компактные manifests/evidence packages и зафиксированные
analysis outputs. Сырые локальные runs, checkpoints и отдельные forensic
артефакты не считаются частью Git release автоматически.

Финальная диссертация использует результаты только через проверяемые
thesis-facing bindings. Главные статусы C01–C11 определяются
`thesis/data/research_claims.json`, а их provenance/section binding —
`thesis/data/thesis_traceability.json` и `scripts/build_thesis_assets.py`.

Основные области:

- Stage 1: `summaries/`, `tables/`, `figures/`;
- Stage 2: `stage-2/` и cross-version comparison;
- Stage 3A: layer-wise gradient/representation outputs;
- Stage 3B: B0, SI-MA0/SI-MA1, B1/B2, matched profiling and analysis;
- QWake: bounded scientific summaries and frozen identifiers consumed by the
  dissertation contract.

Файл в этом каталоге сам по себе не меняет claim status. Статус
`supported/rejected/descriptive/not_tested` возникает только через
зарегистрированный decision contract и финальную thesis reconciliation.

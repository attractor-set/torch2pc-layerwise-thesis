# `ADR-039`: `FixedPred` `sufficiency` и `DONE / UNKNOWN / SWEEP`

[English version](ADR-039-stage3b-fixedpred-sufficiency-dus-design_EN.md)

- **Статус:** принято как проектная фиксация без разрешения [выполнения](../glossary.md#term-execution)
- **Дата:** 2026-07-23

## Контекст

`EX-IF0` выбрал `stage2_baseline` как `canonical` `exact` `reference` и `fail-closed`
`fallback`. Последующая проверка уточнила:

1. `B0` измеряет `context-dependent` `cost` `surface`, а не разные `prefix` `budgets`.
2. `B1`/`B2` совпадают по номинальной аллокации, а не по реализованной стоимости.
3. Сохранение математики формулируется отдельно внутри `FixedPred` и `Strict`.
4. `Joint-VJP` является `exact` `graph-organization` `control`, а не шоткатом.
5. Частный случай `Rosenbaum` является аналитическим `positive` `control`.

## Решение

1. Обязательный метод следующего этапа — `FixedPred`.
2. `Exact` `graph` и `oracle` `source` — `stage2_baseline`.
3. `Temporal` `prefix` `study` является обязательным ядром.
4. `Spatial` `recursive` `aggregates` остаются условным расширением.
5. `Oracle` `alphabet`: `sufficient / insufficient`.
6. `Shadow` `alphabet`: `DONE / UNKNOWN / SWEEP`.
7. `DONE` требует положительного `sufficiency` `admission`.
8. Неразрешённый `UNKNOWN` завершается `SWEEP`.
9. `Compute` и `diagnostic` `budgets` учитываются раздельно.
10. Метрики применяются в порядке `safety` → `coverage` → `cost`.
11. `Greedy` `acquisition` остаётся `shadow-only` `demonstrator`.
12. `Joint-VJP` не входит в `action` `alphabet`.
13. `Rosenbaum` `control` не заменяет `EX-IF0`.
14. [Выполнение](../glossary.md#term-execution), `oracle-label` `generation`, `feature` `collection`, `policy` `activation`
    и `test` `access` остаются закрытыми.

## Машинная граница

```text
fixedpred_sufficiency_dus_design_frozen=true
fixedpred_sufficiency_method=fixedpred
fixedpred_sufficiency_exact_graph=stage2_baseline
rosenbaum_wavefront_role=analytic_positive_control
joint_vjp_role=exact_graph_organization_control
dus_controls_execution=false
oracle_label_generation_open=false
feature_collection_permitted=false
a11_off0_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

## Следствие

Следующий допустимый `slice` ограничен рефакторингом и `synthetic` `validation`.
Научное выполнение требует отдельных `contract`, `preflight` и `authorization`.

# `Stage` 3`B`: `FixedPred` `sufficiency` и `D`/`U`/`S`

[English version](STAGE3B-FIXEDPRED-SUFFICIENCY-DUS_EN.md)

**Статус:** план; выполнение не разрешено.

## Назначение плана

План задаёт последовательность, в которой каждый следующий шаг открывается
только отдельным проверяемым решением. Проектная фиксация не разрешает сбор
новых научных данных. Реализация сборщика не разрешает его запуск. Завершение
сбора не разрешает менять семейство метрик после просмотра сравнительных
результатов. Теневой повтор не разрешает управлять реальным вычислением.
Итоговая проверка на закрытой выборке возможна только после отдельной фиксации
кода, признаков, порогов, стоимости и статистического правила.

Такая последовательность сохраняет отрицательные результаты. Если ранняя
достаточность не обнаружена, дешёвые признаки её не распознают или стоимость
диагностики превышает предотвращаемое вычисление, соответствующая ветвь
закрывается без замены критерия после получения результата.

## Этапы

1. `DUS-0`: `design` `freeze`.
2. `DUS-1`: рефакторинг и `synthetic` `validation`.
3. `DUS-2`: `Rosenbaum` `analytic` `positive` `control`.
4. `DUS-3`: отдельная фиксация `A11-OFF0`.
5. `DUS-4`: `policy-neutral` `collector` `implementation`.
6. `DUS-5`: `runtime` `preflight` и `authorization`.
7. `DUS-6`: `oracle` `collection`.
8. `DUS-7`: `post-collection`/`pre-analysis` `freeze`.
9. `DUS-8`: `sufficiency` `opportunity` `analysis`.
10. `DUS-9`: `nested` `representation` `screening`.
11. `DUS-10`: `deterministic` `shadow` `replay`.
12. `DUS-11`: условная `confirmatory` `evaluation`.
13. `DUS-12`: интеграция диссертации.

## `Oracle` `collection`

Для каждого `snapshot` будущий разрешённый `collector` должен:

1. сохранить `pre-action` `representation`;
2. выполнить полный `canonical` `suffix`;
3. вычислить $M^*(t)$;
4. определить $t^*$;
5. измерить полный `cost` `vector`;
6. сохранить `provenance`.

`Policy` не управляет выполнением.

## Представления

```text
phi_0 structural
phi_1 magnitude
phi_2 temporal
phi_3 PC-CATM
phi_4 compact directional
```

## Решения анализа

```text
early_sufficiency_present
no_early_sufficiency
state_dependent
static_only
diagnostically_observable
diagnostically_unobservable
cost_feasible
cost_infeasible
```

## Инварианты

```text
dangerous_done_count=0
post_action_feature_leakage=0
observer_interference_events=0
budget_overspend_events=0
post_terminal_acquisition_events=0
controls_execution=false
test_dataset_access=false
```

## Отрицательные маршруты

Допустимы отсутствие раннего `sufficient` `prefix`, отсутствие дешёвой
наблюдаемости, `cost-infeasible` `diagnostics`, отсутствие `state` `dependence`,
отсутствие `incremental` `value` `PC-CATM` и отсутствие преимущества `greedy`
`routing`.

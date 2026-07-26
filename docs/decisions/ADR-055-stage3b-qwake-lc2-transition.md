# ADR-055: переход к `QW-LC2`

[English version](ADR-055-stage3b-qwake-lc2-transition_EN.md)

- Статус: принято
- Дата: 26 июля 2026 года

## Контекст

Фиксация состояния репозитория `QW-LC1` слита в `main` коммитом
`9d073bc3c90eeda53ca03d0f7762b65da8749269` и независимо проверена. Это завершает `QW-LC1` и разрешает
только отдельный переход к проектированию модели ресурсов `QW-LC2`.

`QW-LC2` должен связать [ресурсную траекторию](../glossary.md#term-resource-trajectory)
`Γ(a,s)` с [вектором стоимости](../glossary.md#term-cost-vector) `C(a,s)` через
отображение `Φ`, а затем определить отдельный оператор
[эквивалентности по стоимости](../glossary.md#term-cost-equivalence) `~C`.

## Решение

1. Материализовать двухфайловую квитанцию перехода
   `stage3b-qwake-lc2-transition-v1`.
2. Связать её с коммитом слияния `main`, фиксацией состояния репозитория `QW-LC1`,
   схемой `R(a,s)` и их точными контрольными суммами.
3. Ограничить будущий контракт `QW-LC2` тремя взаимосвязанными частями:
   - измерительная схема `Γ(a,s)`;
   - отображение `Φ: Γ -> C` с запретом двойного учёта;
   - `~C`, [Pareto-допустимость](../glossary.md#term-pareto-admissibility) и зарегистрированное разрешение неоднозначности.
4. Не задавать в переходе поля, единицы, окна, пороги, агрегацию,
   скаляризацию или эмпирические значения стоимости.
5. Отложить сопоставленную теневую проверку, идентичность состояния, состояние
   генераторов случайных чисел, резервный путь, реализацию и
   [выполнение](../glossary.md#term-execution) до последующих срезов.
6. До слияния перехода оставить `QW-LC2` и все три определения закрытыми.

## Проверяемая граница

```text
qwake_qw_lc1_complete=true
qwake_qw_lc2_transition_permitted=true
qwake_qw_lc2_transition_materialized=true
qwake_qw_lc2_transition_complete=false
qwake_qw_lc2_open=false
resource_trajectory_schema_open=false
measurement_to_cost_mapping_open=false
cost_equivalence_operator_definition_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC2-transition-merge
qwake_post_merge_next_slice=QW-LC2-resource-cost-contract
```

## Последствия

После слияния и отдельной проверки после слияния может быть открыта ветка
контракта ресурсов и стоимости. Этот ADR не является моделью измерений, не
утверждает превосходство механизма и не разрешает вычислительные действия.

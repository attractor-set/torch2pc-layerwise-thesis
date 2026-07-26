# ADR-052: переход к `QW-LC1`

[English version](ADR-052-stage3b-qwake-lc1-transition_EN.md)

- Статус: принято
- Дата: 26 июля 2026 года

## Контекст

Фиксация состояния репозитория `QW-LC0` слита в `main` коммитом
`0fbd54be337665e06ad63b6d9c7f8ca978ab75ee` и прошла повторную проверку. Это завершает
предшествующий барьер и разрешает отдельный переход к проектированию
`QW-LC1`, но не открывает содержимое `QW-LC1` до слияния данной квитанции.

`QW-LC1` предназначен только для фиксации канонической схемы
[требуемого результата](../glossary.md#term-required-result) `R(a,s)`,
обязательных наблюдаемых полей и оператора
[эквивалентности ответов](../glossary.md#term-response-equivalence) `~R`.

## Решение

1. Материализовать двухфайловую квитанцию перехода
   `stage3b-qwake-lc1-transition-v1`.
2. Связать её с коммитом слияния `main`, фиксацией состояния репозитория
   `QW-LC0`, контрактом семантики и их точными контрольными суммами.
3. Зафиксировать конечную область будущего `QW-LC1`:
   - каноническая схема `R(a,s)`;
   - обязательные наблюдаемые поля;
   - оператор `~R`.
4. Отложить схему траектории `Γ`, отображение `Φ`, [вектор стоимости](../glossary.md#term-cost-vector) `C`,
   реализацию, проверку ограниченного аналитического случая и
   [выполнение](../glossary.md#term-execution) до последующих срезов.
5. До слияния перехода оставить `QW-LC1` и его схему требуемого результата
   закрытыми.

## Проверяемая граница

```text
qwake_qw_lc0_repository_freeze_complete=true
qwake_qw_lc1_transition_permitted=true
qwake_qw_lc1_transition_materialized=true
qwake_qw_lc1_transition_complete=false
qwake_qw_lc1_open=false
qwake_qw_lc1_required_response_schema_open=false
mandatory_observables_definition_open=false
response_equivalence_operator_definition_open=false
resource_trajectory_schema_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC1-transition-merge
qwake_post_merge_next_slice=QW-LC1-required-response-schema
```

## Последствия

После слияния и отдельной проверки после слияния может быть открыта ветка
проектирования `QW-LC1`. Этот ADR не определяет поля схемы, допуски `~R`,
измерения `Γ`, стоимость, код или вычислительную кампанию.

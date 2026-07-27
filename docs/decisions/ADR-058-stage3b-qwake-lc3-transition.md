# ADR-058: переход к `QW-LC3`

[English version](ADR-058-stage3b-qwake-lc3-transition_EN.md)

- Статус: принято
- Дата: 26 июля 2026 года

## Контекст

Фиксация состояния репозитория `QW-LC2` слита в `main` коммитом
`4f7c533047214398e7ec4dde9d58b5fc06964b90` и независимо проверена. Коммит
фиксации `3f4310a05de5b7cd3db0cdb5c8f7cf4bbcb09150` сохранён в графе слияния,
дерево не изменено, а квитанция и контракт ресурсов имеют ожидаемые
контрольные суммы. Это завершает `QW-LC2` и разрешает только отдельный переход
к проектированию сопоставленной проверки `QW-LC3`.

`QW-LC3` должен связать уже зафиксированные [требуемый результат](../glossary.md#term-required-result)
`R(a,s)` и [вектор стоимости](../glossary.md#term-cost-vector) `C(a,s;r,p)` с
протоколом,
который сравнивает `LOCAL_SWEEP` и `ANALYTIC_COMPLETION` из одного состояния,
восстанавливает генераторы случайных чисел и сохраняет полный точный резервный
суффикс.

## Решение

1. Материализовать двухфайловую квитанцию перехода
   `stage3b-qwake-lc3-transition-v1`.
2. Связать её с коммитом слияния `main`, фиксацией состояния репозитория
   `QW-LC2`, контрактом ресурсов и стоимости, схемой требуемого результата и их
   точными контрольными суммами.
3. Ограничить будущий контракт `QW-LC3` следующими частями:
   - протоколом сопоставленной теневой проверки;
   - построением и проверкой непрозрачной ссылки на общее состояние;
   - снимком, восстановлением и проверкой состояния генераторов случайных
     чисел;
   - проверкой полного точного резервного суффикса;
   - порядком повторов и сопоставленной агрегацией.
4. Не задавать в переходе сериализацию снимка, список генераторов, порядок рук,
   число повторов, допуски, агрегаторы, окна измерений или критерии успешного
   результата.
5. Не открывать реализацию кандидата, разрешение на
   [выполнение](../glossary.md#term-execution), инженерную проверку, сбор
   признаков, создание эталонных меток, активацию политики, научную кампанию,
   тестовую выборку или публикацию.
6. До слияния перехода оставить `QW-LC3` и все его определения закрытыми.

## Проверяемая граница

```text
qwake_qw_lc2_repository_freeze_complete=true
qwake_qw_lc2_complete=true
qwake_qw_lc3_transition_permitted=true
qwake_qw_lc3_transition_materialized=true
qwake_qw_lc3_transition_complete=false
qwake_qw_lc3_open=false
matched_shadow_validation_protocol_open=false
opaque_state_ref_definition_open=false
rng_restoration_protocol_open=false
exact_reserve_suffix_validation_open=false
repeat_aggregation_protocol_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
qwake_next_slice=QW-LC3-transition-merge
qwake_post_merge_next_slice=QW-LC3-matched-shadow-validation-contract
```

## Последствия

После слияния и отдельной проверки после слияния может быть открыта ветка
контракта сопоставленной теневой проверки. Этот ADR не доказывает
эквивалентность механизмов, не активирует профиль `end_to_end_v1` и не
разрешает вычислительные действия.

# ADR-054: фиксация состояния репозитория `QW-LC1`

[English version](ADR-054-stage3b-qwake-lc1-repository-freeze_EN.md)

- Статус: принято
- Дата: 26 июля 2026 года

## Контекст

Контракт `stage3b-qwake-lc1-required-response-schema-v1` записан коммитом
`de2b5a37583b22946073390caa244bee35dd793b` и слит в `main` коммитом слияния
`59e3143ba105a5b298e2cd551b221b8f6dae96f7`. Проверка после слияния подтвердила первого и второго
родителей, точный 22-файловый состав, неизменность дерева схемы и контрольных
сумм контракта и реестра.

Перед завершением `QW-LC1` требуется отдельная
[фиксация целостности](../glossary.md#term-integrity-sealing), которая связывает
проверенную схему с конкретным состоянием `main`. Эта фиксация не определяет
`Γ`, `Φ`, стоимость или `~C` и не разрешает следующий срез до собственного
слияния и повторной проверки.

## Решение

1. Материализовать двухфайловую квитанцию состояния репозитория `QW-LC1`.
2. Связать её с точными коммитами `main`, схемы и предшествующего перехода.
3. Зафиксировать точные контрольные суммы контракта и его реестра.
4. Сохранить схему и все предшествующие
   [доказательные материалы](../glossary.md#term-evidence) неизменными.
5. До слияния квитанции оставить `QW-LC1` незавершённым и запретить переход к
   `QW-LC2`.
6. Не открывать ресурсную траекторию, отображение стоимости, реализацию,
   [выполнение](../glossary.md#term-execution), сбор признаков, создание
   эталонных меток, научный образ, тестовую выборку или публикацию.

## Проверяемая граница

```text
qwake_qw_lc1_required_response_schema_merged=true
qwake_qw_lc1_schema_main_commit=59e3143ba105a5b298e2cd551b221b8f6dae96f7
qwake_qw_lc1_schema_commit=de2b5a37583b22946073390caa244bee35dd793b
qwake_qw_lc1_repository_freeze_materialized=true
qwake_qw_lc1_repository_freeze_complete=false
qwake_qw_lc1_complete=false
qwake_qw_lc2_transition_permitted=false
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
qwake_next_slice=QW-LC1-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC2-transition
```

## Последствия

После слияния требуется отдельная проверка квитанции на `main`. Только её успех
может завершить `QW-LC1` и разрешить самостоятельный переход к `QW-LC2`;
ресурсная схема, стоимость, код и выполнение этим решением не открываются.

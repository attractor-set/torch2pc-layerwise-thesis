# ADR-060: фиксация состояния репозитория `QW-LC3`

[English version](ADR-060-stage3b-qwake-lc3-repository-freeze_EN.md)

- Статус: принято
- Дата: 27 июля 2026 года

## Контекст

Контракт `stage3b-qwake-lc3-matched-shadow-validation-contract-v1` записан
коммитом `fb3f1cd4a4d3b4261db1179badcc1ccacddfe936` и слит через PR №121 в `main`
`71e73f56408c720334b8fa03e7133762c8bbcc43`. Проверка после слияния подтвердила точных
родителей, 14-файловый состав, неизменность дерева и контрольных сумм.

Перед завершением `QW-LC3` отдельная
[фиксация целостности](../glossary.md#term-integrity-sealing) должна связать
проверенный контракт с конкретным состоянием `main`.

## Решение

1. Материализовать двухфайловую квитанцию состояния репозитория `QW-LC3`.
2. Связать её с точными коммитами `main`, контракта и перехода `QW-LC3`.
3. Зафиксировать контрольные суммы контракта, его реестра и квитанции перехода.
4. Сохранить предшествующие
   [доказательные материалы](../glossary.md#term-evidence) неизменными.
5. До слияния и повторной проверки оставить `QW-LC3` незавершённым и
   реализацию `QW-LC4-I` запрещённой.
6. Не открывать реализацию, [выполнение](../glossary.md#term-execution),
   сбор признаков, эталонные метки, тестовую выборку или публикацию.

## Проверяемая граница

```text
qwake_qw_lc3_matched_shadow_validation_contract_merged=true
qwake_qw_lc3_matched_shadow_validation_contract_complete=true
qwake_qw_lc3_contract_id=stage3b-qwake-lc3-matched-shadow-validation-contract-v1
qwake_qw_lc3_contract_sha256=sha256:e1512f29b3e3e3882001172df360e895e6e628b8ea8e4103b9574990775dd5d8
qwake_qw_lc3_repository_main_commit=71e73f56408c720334b8fa03e7133762c8bbcc43
qwake_qw_lc3_contract_commit=fb3f1cd4a4d3b4261db1179badcc1ccacddfe936
qwake_qw_lc3_repository_freeze_materialized=true
qwake_qw_lc3_repository_freeze_complete=false
qwake_qw_lc3_complete=false
qwake_qw_lc4_implementation_permitted=false
matched_shadow_validation_protocol_frozen=true
opaque_state_ref_definition_frozen=true
rng_restoration_protocol_frozen=true
exact_reserve_suffix_validation_frozen=true
repeat_aggregation_protocol_frozen=true
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
qwake_next_slice=QW-LC3-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC4-I
```

## Последствия

Только проверка квитанции после её слияния может завершить `QW-LC3` и
разрешить отдельную реализацию `QW-LC4-I`. Выполнение и научная кампания
останутся закрытыми до собственных последующих границ.

# ADR-057: фиксация состояния репозитория `QW-LC2`

[English version](ADR-057-stage3b-qwake-lc2-repository-freeze_EN.md)

- Статус: принято
- Дата: 26 июля 2026 года

## Контекст

Контракт `stage3b-qwake-lc2-resource-cost-contract-v1` записан коммитом `3f1682765089b0819dcaaf9bb449c4c1bd155142` и слит в
`main` коммитом слияния `8f24229bcf19736086fe6f0340bda26dd533936a`. Проверка после слияния подтвердила точных
родителей, 20-файловый состав, неизменность дерева и контрольных сумм.

Перед завершением `QW-LC2` отдельная
[фиксация целостности](../glossary.md#term-integrity-sealing) должна связать
проверенный контракт с конкретным состоянием `main`.

## Решение

1. Материализовать двухфайловую квитанцию состояния репозитория `QW-LC2`.
2. Связать её с точными коммитами `main`, контракта и перехода `QW-LC2`.
3. Зафиксировать контрольные суммы контракта, реестра и квитанции перехода.
4. Сохранить предшествующие
   [доказательные материалы](../glossary.md#term-evidence) неизменными.
5. До слияния и повторной проверки оставить `QW-LC2` незавершённым и
   переход к `QW-LC3` запрещённым.
6. Не открывать реализацию, [выполнение](../glossary.md#term-execution),
   сбор признаков, эталонные метки, тестовую выборку или публикацию.

## Проверяемая граница

```text
qwake_qw_lc2_resource_cost_contract_merged=true
qwake_qw_lc2_resource_cost_contract_complete=true
qwake_qw_lc2_contract_id=stage3b-qwake-lc2-resource-cost-contract-v1
qwake_qw_lc2_contract_sha256=sha256:313dc969ab59db20ee27976d3158fca23ce511801e0dc7700dde0d2d002ab69d
qwake_qw_lc2_repository_main_commit=8f24229bcf19736086fe6f0340bda26dd533936a
qwake_qw_lc2_resource_cost_commit=3f1682765089b0819dcaaf9bb449c4c1bd155142
qwake_qw_lc2_repository_freeze_materialized=true
qwake_qw_lc2_repository_freeze_complete=false
qwake_qw_lc2_complete=false
qwake_qw_lc3_transition_permitted=false
resource_trajectory_schema_frozen=true
measurement_to_cost_mapping_frozen=true
cost_equivalence_operator_definition_frozen=true
pareto_and_tie_break_rule_frozen=true
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
qwake_next_slice=QW-LC2-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC3-transition
```

## Последствия

Только проверка квитанции после её слияния может завершить `QW-LC2` и
разрешить отдельный переход к `QW-LC3`. Реализация и выполнение закрыты.

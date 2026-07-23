# `ADR-040`: интегрированная модель фронтира

[English version](ADR-040-stage3b-integrated-frontier-model_EN.md)

- **Статус:** принято как проектная фиксация после `ADR-039`; [выполнение](../glossary.md#term-execution) не разрешено
- **Дата:** 2026-07-23

## Контекст

`ADR-039` зафиксировал `DONE / UNKNOWN / SWEEP`, раздельные вычислительный и
диагностический бюджеты и закрытую при ошибке семантику. Последующее уточнение
обнаружило две перегрузки:

1. `UNKNOWN` одновременно обозначал недостаток знания и переход к следующей
   аналитике;
2. `SWEEP` мог читаться как один следующий свип или как полный резервный
   суффикс.

Одновременно требовалось встроить уровни наблюдения `A0 / A1 / A2` и их
стоимость, не смешивая семантику `PC-TREF`, механизм `PC-CATM` и оркестрацию
`QWake-PC`.

## Решение

1. Сохранить `ADR-039` неизменным как предшествующий нормативный слой.
2. Ввести интегрированный фронтир, объединяющий вычислительный снимок,
   накопительное `pre-action` представление, два остатка бюджета и происхождение.
3. Зафиксировать уровни `A0` — структурные признаки, `A1` — дешёвые редукции на
   устройстве, `A2` — локальные редукции на вложенной детерминированной
   подвыборке; `O` оставить только `post-action oracle`.
4. Ввести алфавит действий
   `ACCEPT_FRONTIER / ADVANCE_FRONTIER / COMPLETE_SUFFIX`.
5. Разрешать `ACCEPT_FRONTIER` только после положительного `PC-TREF`-допуска.
6. Определить `ADVANCE_FRONTIER` как ровно один зарегистрированный смежный
   переход наблюдения или один канонический свип.
7. Определить `COMPLETE_SUFFIX` как единственный полный `fail-closed` резервный
   путь `stage2_baseline`.
8. Отображать `DONE` в кандидата `ACCEPT_FRONTIER`, `UNKNOWN` — в эпистемическое
   состояние, а одношаговый `SWEEP` — в `ADVANCE_FRONTIER(compute)`.
9. Относить полный [вектор стоимости](../glossary.md#term-cost-vector) к каждому ребру фронтира и отдельно
   учитывать стоимость создания `O`.
10. Требовать вложенную детерминированную выборку, разделение `pre-action` и
    `post-action`, невмешательство и полное происхождение.
11. Зафиксировать `PC-TREF` как слой допуска, `PC-CATM` как источник механизмных
    свидетельств, а `QWake-PC` как будущую оркестрацию переходов.
12. Оставить модель детерминированной, офлайн и `shadow-only`.
13. Не открывать создание меток, сбор признаков, `A11-OFF0`, рекурсивные
    агрегаты, политику или тестовую выборку.

## Машинная граница

```text
integrated_frontier_model_frozen=true
frontier_action_alphabet=ACCEPT_FRONTIER,ADVANCE_FRONTIER,COMPLETE_SUFFIX
observation_level_order=A0,A1,A2,O
nested_deterministic_sampling_required=true
pre_action_post_action_separation_required=true
observer_non_interference_required=true
frontier_edge_cost_vector_required=true
oracle_cost_separate_from_deployable_cost=true
pc_tref_role=admission_semantics
pc_catm_role=mechanism_evidence
qwake_pc_role=frontier_orchestration
integrated_frontier_controls_execution=false
oracle_label_generation_open=false
feature_collection_permitted=false
a11_off0_execution_open=false
recursive_aggregate_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

## Следствие

Следующий допустимый `slice` ограничен чистыми типами фронтира, реестром
смежных переходов, детерминированным семплированием, учётом стоимости и
синтетическими проверками невмешательства. Научный сбор требует отдельного
контракта, `runtime` `preflight` и авторизации.

# `ADR-041`: корректирующая семантика интегрированного фронтира

[English version](ADR-041-stage3b-integrated-frontier-corrective-semantics_EN.md)

- **Статус:** принято как корректирующая проектная фиксация после `ADR-040`; [выполнение](../glossary.md#term-execution) не разрешено
- **Дата:** 2026-07-23

## Контекст

`ADR-039` зафиксировал семантику `DONE / UNKNOWN / SWEEP`, а `ADR-040` ввёл
интегрированный фронтир. Последующий аудит выявил пять областей, требующих
уточнения без ретроспективного переписывания принятых решений:

1. `O` был записан в один порядок с развёртываемыми уровнями `A0 / A1 / A2`,
   хотя является только `post-action oracle`;
2. глобальная формулировка монотонности противоречила переходу к новому снимку
   с базовым наблюдением `A0`;
3. измерительный и решенческий векторы стоимости не были связаны явным
   отображением;
4. `DONE` одновременно читался как прошедший допуск результат и как [кандидат](../glossary.md#term-candidate) на
   допуск;
5. алфавит переходов не выделял дешёвый аналитический шаг как самостоятельный
   способ продвижения фронтира.

Аудит границы новизны также показал, что адаптивная остановка, приобретение
признаков, `selective prediction`, `value of computation` и апостериорные
сертификаты являются предшествующими направлениями. Собственный проверяемый
вклад должен ограничиваться их протокольно управляемой интеграцией для
частичной траектории обучения `FixedPred` относительно полного точного
суффикса.

## Решение

1. Сохранить `ADR-039` и `ADR-040` неизменными историческими решениями.
2. Установить `ADR-041` нормативным для текущей интерпретации переходов,
   допуска, стоимости, границы `oracle` и обязательного исследовательского
   `scope`.
3. Ограничить развёртываемую ось наблюдения порядком `A0 -> A1 -> A2`.
   Уровень `O` учитывать отдельно как `post-action oracle`, недоступный любому
   предложению действия.
4. Представлять фронтир как
   `F(t, A_i, H)`, где `H` — неизменяемая история полученных аналитических
   результатов и сертификатов.
5. Сохранить верхнеуровневый алфавит
   `ACCEPT_FRONTIER / ADVANCE_FRONTIER / COMPLETE_SUFFIX`, но разделить
   `ADVANCE_FRONTIER` на смежные виды `OBSERVATION`, `ANALYTIC` и `COMPUTE`.
6. Разрешить аналитический переход до первого свипа, между свипами или вместо
   следующего свипа, если он заранее зарегистрирован, использует только
   `pre-action` данные и его стоимость измеряется.
7. Различать точный сертификат, консервативную гарантированную границу и
   статистическую/эвристическую оценку. Последняя не может непосредственно
   разрешить `ACCEPT_FRONTIER` и требует замороженной процедуры контроля риска.
8. Определить монотонность локально: внутри одного снимка уровень наблюдения и
   история аналитик только расширяются. Переход `COMPUTE` создаёт новый снимок
   `t+1` с текущим уровнем `A0`, сохраняя `append-only` происхождение и историю.
9. Разделить необработанный измерительный вектор ребра и решенческий вектор
   стоимости. Требовать заранее замороженное отображение между ними, запретить
   неявную скаляризацию и двойной учёт.
10. Считать `DONE` уже допущенным теневым исходом `ADR-039`.
    Недопущенная запись называется только `accept_candidate` и не является
    действием. Положительный `PC-TREF`-допуск переводит её в `DONE`, после чего
    каноническая теневая интерпретация — `ACCEPT_FRONTIER`.
11. Ограничить обязательное магистерское ядро временными префиксами одного
    `stage2_baseline`, уровнями `A0 / A1 / A2`, конечным замороженным реестром
    аналитических шагов, детерминированным `shadow replay` и
    `COMPLETE_SUFFIX`.
12. Оставить пространственные рекурсивные агрегаты, `learned routing`,
    `spike-like dynamics` и `active control` условными расширениями.
13. Зарегистрировать обязательные сравнения с полным суффиксом, фиксированным
    числом свипов, простым порогом `prediction error/residual`, `A0-only`,
    фиксированной каскадой `A0 -> A1 -> A2`, детерминированным аналитическим
    реестром, `cheapest-first` и `offline-oracle upper bound`.
14. Не открывать научный сбор, создание `oracle`-меток, `A11-OFF0`, выполнение
    рекурсивных агрегатов, активацию политики или тестовую выборку.

## Нормативное первенство

```text
adr039_authority=dus_outcome_semantics
adr040_authority=historical_integrated_frontier_design
adr041_authority=current_transition_admission_cost_and_scope_semantics
adr041_refines_adr040_fields=observation_oracle_boundary,transition_kinds,monotonicity,cost_mapping,admission,mandatory_scope
historical_adr_rewrite_permitted=false
```

## Машинная граница

```text
integrated_frontier_corrective_semantics_frozen=true
frontier_action_alphabet=ACCEPT_FRONTIER,ADVANCE_FRONTIER,COMPLETE_SUFFIX
frontier_advance_kinds=OBSERVATION,ANALYTIC,COMPUTE
deployable_observation_level_order=A0,A1,A2
oracle_level=O
oracle_availability=post_action_only
oracle_is_frontier_action=false
oracle_is_analytic_step=false
frontier_state_schema=F(t,A_i,H)
within_snapshot_observation_monotone=true
within_snapshot_analytic_history_monotone=true
compute_transition_resets_current_observation=A0
acquisition_history_append_only=true
provenance_monotone=true
analytic_registry_finite_and_frozen=true
analytic_steps_pre_action_only=true
analytic_step_is_not_free=true
exact_or_conservative_certificate_may_support_admission=true
heuristic_analytic_direct_accept=false
statistical_estimate_requires_frozen_risk_admission=true
done_semantics=admitted_shadow_outcome
accept_candidate_is_action=false
accept_frontier_requires_positive_admission=true
edge_measurement_vector_required=true
decision_cost_vector_required=true
measurement_to_decision_cost_mapping_required=true
implicit_cost_scalarization_forbidden=true
cost_double_counting_forbidden=true
mandatory_thesis_scope=temporal_fixedpred_prefix
recursive_multiscale_scope=conditional_extension
active_control_scope=outside_mandatory_core
integrated_frontier_controls_execution=false
oracle_label_generation_open=false
feature_collection_permitted=false
a11_off0_execution_open=false
recursive_aggregate_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

## Граница предшествующих работ и утверждений

Адаптивная остановка `predictive coding` имеет прямой соседний пример в
[Hybrid Predictive Coding](https://doi.org/10.1371/journal.pcbi.1011280).
Общие механизмы `adaptive computation`, `active feature acquisition`, `selective prediction` и выбора внутренних вычислений представлены соответственно в
[Adaptive Computation Time](https://arxiv.org/abs/1603.08983),
[Joint Active Feature Acquisition](https://proceedings.neurips.cc/paper_files/paper/2018/hash/e5841df2166dd424a57127423d276bbe-Abstract.html),
[SelectiveNet](https://proceedings.mlr.press/v97/geifman19a.html) и
[Learning to select computations](https://arxiv.org/abs/1711.06892).

Поэтому пакет не заявляет первенство отдельных механизмов. Проверяемая
граница вклада — `protocol-first` интеграция `task-relative sufficiency`,
внутреннего приобретения диагностик, аналитических сертификатов и
`risk-controlled adaptive computation` для частичных `FixedPred` `training trajectories` относительно `exact canonical suffix`.

## Следствие

Следующий допустимый `slice` ограничен чистыми типами, конечным реестром
смежных переходов, синтетическими сертификатами, явным отображением стоимости,
невмешательством и `regression guards`. Научное выполнение требует отдельного
контракта, `runtime preflight` и авторизации.

# Этап 3B: интегрированная модель фронтира

[English version](stage3b-integrated-frontier-model_EN.md)

**Статус:** консолидированная проектная фиксация с учётом `ADR-041`; [выполнение](glossary.md#term-execution), создание `oracle`-меток, сбор признаков и управление остаются закрытыми.

## 1. Назначение и нормативная иерархия

Документ объединяет действующую семантику исследования достаточности
`FixedPred`, стоимости наблюдения, дешёвых аналитических шагов и будущей
оркестрации `QWake-PC`. Он не меняет математическую динамику `FixedPred`,
точный эталон `stage2_baseline` или `EX-IF0`.

Нормативные роли разделены:

```text
ADR-039 = исходы DONE / UNKNOWN / SWEEP
ADR-040 = историческая первая фиксация интегрированного фронтира
ADR-041 = текущая семантика переходов, допуска, стоимости и scope
ADR-042 = QWake-FP validation scope и единый permission-gated image protocol
```

`ADR-039` и `ADR-040` не переписываются. При расхождении в переходах,
допуске и стоимости применяется `ADR-041`; для объекта экспериментальной
проверки, `campaign` `roles` и `image`/`permission` `protocol` применяется `ADR-042`.

## 2. Разделение архитектурных уровней

```text
PC-TREF  = семантика достаточности, допустимого regret и допуска
PC-CATM  = механизмная модель и источник интерпретируемых свидетельств
QWake-PC = будущая оркестрация зарегистрированных переходов
executor = каноническая траектория stage2_baseline
```

`PC-TREF` определяет, допустимо ли принять текущий фронтир относительно
зарегистрированного конечного ответа. `PC-CATM` может предоставить признаки,
точные тождества или консервативные границы, но не разрешает действие сам по
себе. `QWake-PC` выбирает только среди заранее зарегистрированных переходов и
до отдельного допуска работает с `controls_execution=false`.

## 3. Состояние фронтира

Для обязательного временного пути состояние задаётся как

```math
\mathcal F_{t,i,H}=\left(
S_t,R_{A_i},H,B^{\mathrm{compute}}_{\mathrm{rem}},
B^{\mathrm{diag}}_{\mathrm{rem}},P
\right),
```

где:

- $S_t$ — неизменяемый снимок после $t$ канонических свипов;
- $R_{A_i}$ — накопительное `pre-action` представление;
- $H$ — `append-only` история полученных аналитических результатов и
  сертификатов;
- два бюджета разделяют дальнейшее вычисление и получение свидетельств;
- $P$ — происхождение модели, данных, `RNG`, графа и реализации.

Обязательное ядро использует только временные префиксы одного
`stage2_baseline`. Пространственные рекурсивные агрегаты остаются условным
расширением.

## 4. Наблюдение и `oracle`

Развёртываемая ось имеет ровно три вложенных уровня:

```text
A0 -> A1 -> A2
```

- `A0` содержит структурные поля без чтения значений тензоров;
- `A1` добавляет конечный набор дешёвых редукций на устройстве;
- `A2` добавляет локальные редукции на вложенной детерминированной
  подвыборке.

Накопительные представления:

```text
R_A0 = A0
R_A1 = A0 + A1
R_A2 = A0 + A1 + A2
```

`O` не является четвёртым уровнем наблюдения. Он создаётся только после
действия полным каноническим суффиксом, не входит в `deployable representation`,
не является переходом и никогда не передаётся теневому контроллеру.

## 5. Алфавит действий и переходов

Верхнеуровневый алфавит остаётся компактным:

```text
ACCEPT_FRONTIER
ADVANCE_FRONTIER
COMPLETE_SUFFIX
```

`ADVANCE_FRONTIER` выполняет ровно один смежный переход одного из видов:

```text
OBSERVATION = приобрести следующий A-уровень при неизменном S_t
ANALYTIC    = выполнить один зарегистрированный pre-action аналитический шаг
COMPUTE     = выполнить один следующий канонический свип
```

Аналитический шаг разрешён до первого свипа, между свипами или вместо
следующего свипа, если его входы доступны до действия, он входит в конечный
замороженный реестр и его стоимость измеряется. `O` не является аналитическим
шагом.

`COMPLETE_SUFFIX` выполняет весь оставшийся `stage2_baseline` и является
единственным `fail-closed` резервным путём.

## 6. Аналитические результаты и допуск

Различаются три класса результатов:

1. **точный сертификат** — доказанное тождество или точное условие;
2. **консервативный сертификат** — гарантированная верхняя граница,
   достаточная для зарегистрированного допуска;
3. **статистическая или эвристическая оценка** — эмпирический сигнал без
   прямой гарантии.

Точный или консервативный сертификат может поддержать `PC-TREF`-допуск.
Статистическая оценка требует отдельно замороженной процедуры контроля риска и
не может напрямую разрешить `ACCEPT_FRONTIER`.

`accept_candidate` — запись, предлагаемая процедуре допуска, а не действие.
После положительного допуска исход `ADR-039` равен `DONE`, и только тогда его
теневая `action`-интерпретация равна `ACCEPT_FRONTIER`.

```text
accept_candidate -> PC-TREF admission -> DONE -> ACCEPT_FRONTIER
```

`UNKNOWN` остаётся эпистемическим состоянием. `SWEEP` в исторической семантике
означает один следующий канонический свип и отображается в
`ADVANCE_FRONTIER(kind=COMPUTE)`.

## 7. Монотонность и граф переходов

Монотонность действует внутри одного снимка:

- `A0 -> A1 -> A2` не откатывается;
- $H$ только расширяется;
- происхождение не переписывается.

Переход `COMPUTE` создаёт новый снимок и возвращает **текущий** уровень
наблюдения к `A0`, сохраняя `append-only` историю приобретений и происхождение:

```text
F(t,Ai,H) --COMPUTE--> F(t+1,A0,H')
```

Обязательный граф включает:

```text
F(t,A0,H) --OBSERVATION:A1--> F(t,A1,H)
F(t,A1,H) --OBSERVATION:A2--> F(t,A2,H)
F(t,Ai,H) --ANALYTIC:h_j----> F(t,Ai,H+{h_j})
F(t,Ai,H) --COMPUTE---------> F(t+1,A0,H')
F(t,Ai,H) --admitted-------> terminal_shadow_accept
F(t,Ai,H) --full_suffix----> terminal_canonical_reference
```

Неизвестное, недоступное, нарушающее контракт или исчерпавшее бюджет состояние
закрывается через `COMPLETE_SUFFIX`.

## 8. Два уровня стоимости

Сырые измерения ребра сохраняются без потерь:

```text
edge_measurement_vector =
  host_elapsed_ns,
  device_elapsed_ns,
  synchronization_events,
  device_to_host_bytes,
  temporary_peak_bytes,
  persistent_trace_bytes,
  acquisition_count
```

Решенческий вектор сохраняет семантические категории:

```text
decision_cost_vector =
  compute,
  latency,
  memory,
  diagnostic,
  observer,
  control,
  fallback
```

Между ними до анализа фиксируется отображение `g`. Сырые поля не складываются
неявно, одна величина не учитывается дважды, а скаляризация допускается только
как отдельно зарегистрированное правило. Стоимость создания `O` хранится как
исследовательская стоимость разметки и не включается в `deployable diagnostic cost`.

## 9. Невмешательство и временная граница

Наблюдение и аналитика обязаны быть только читающими и не изменять состояние,
параметры, буферы, градиенты, `RNG`, `autograd`-путь или выбор канонической
ветви.

```text
observer_state_mutations=0
observer_parameter_mutations=0
observer_buffer_mutations=0
observer_rng_mutations=0
observer_autograd_path_changes=0
observer_interference_events=0
post_action_feature_leakage=0
```

До действия недоступны $M^*$, $t^*$, конечный `endpoint`, фактическая полезность
следующего свипа и `oracle`-оптимальный переход.

## 10. Обязательные сравнения

Минимальный `confirmatory` пакет должен включать:

```text
B0 full_canonical_suffix
B1 fixed_sweep_budget
B2 registered_prediction_error_or_residual_threshold
B3 A0_only
B4 fixed_A0_A1_A2_cascade
B5 deterministic_analytic_registry
B6 cheapest_first_frontier
B7 offline_oracle_upper_bound
```

`B2` отделяет новый фронтир от простого раннего завершения по `prediction error`.
`B7` не является `deployable policy` и задаёт только верхнюю границу возможности.

## 11. Граница новизны

Адаптивная остановка, `active feature acquisition`, `selective prediction`,
метарассуждение и аналитические сертификаты являются предшествующими
направлениями. Работа не заявляет первенство этих механизмов по отдельности.

Проверяемый вклад ограничен `protocol-first` интеграцией `task-relative sufficiency`, приобретения внутренних диагностик, аналитических сертификатов и
`risk-controlled adaptive computation` для частичных `FixedPred` `training trajectories` относительно `exact canonical suffix`.

## 12. Обязательный `scope`

Обязательное магистерское ядро:

1. общая спецификация `QWake-PC` без утверждения общей эмпирической проверки;
2. одна конкретная [QWake-FP](glossary.md#term-qwake-fp) для исправленного
   `Rosenbaum FixedPred`, `eta=1` и `stage2_baseline`;
3. `temporal` `prefixes`, `A0 / A1 / A2` и конечный аналитический реестр;
4. один `immutable` `superset` `image` для `C1/C2/C3/R`;
5. внутренние `fail-closed` `permission` `gates` на границах эффектов;
6. `frozen` `policy` как `data` `manifest` для встроенного интерпретатора;
7. `deterministic shadow replay`, `safety-first` `admission` и полная стоимость;
8. `COMPLETE_SUFFIX` как `canonical` `fallback`;
9. `untouched` `confirmatory` `seeds`, простые `baselines`, `nested` `ablations` и одна
   `replication` без `retuning`.

`Recursive multiscale aggregates`, `Strict`, `arbitrary` `eta`, `learned` `routing`,
`spike-like dynamics` и `active control` находятся вне обязательного ядра.

## 13. Единый образ и доказательные стадии

`ADR-042` разделяет присутствующий код и разрешённое исполнение. Один образ
заранее содержит полный обязательный `pipeline`, а роли
`C1_COLLECTION / C2_CALIBRATION / C3_CONFIRMATORY / R_REPLICATION` активируют
только зарегистрированные `capabilities` через `permission` `manifest`.

Выключенная `capability` не исполняется и не создаёт `tensor` `read`, `allocation`,
`synchronization`, `trace` или `output`. `SELECT_POLICY` разрешён только в `C2`, а
сочетание `selection` и `confirmatory` `access` запрещено. Стадии связываются `sealed`
`receipts` и одним `image` `digest`.

## 14. Машинная граница

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
qwake_fp_only_mandatory_implementation=true
qwake_fp_validation_case=corrected_rosenbaum_fixedpred_eta1
execution_image_strategy=single_immutable_superset_image
same_image_digest_required_across_c1_c2_c3_r=true
stage_activation=fail_closed_permission_manifest
permission_checks_at_effect_boundaries=true
disabled_capability_executes=false
policy_representation=frozen_data_manifest
policy_selection_with_confirmatory_access_forbidden=true
sealed_receipt_chain_required=true
replication_without_retuning_required=true
qwake_fp_execution_permitted=false
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
```

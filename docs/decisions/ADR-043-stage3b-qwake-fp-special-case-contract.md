# ADR-043: заморозка контракта особого случая `QWake-FP`

[English version](ADR-043-stage3b-qwake-fp-special-case-contract_EN.md)

- **Статус:** принято как `QW-2`; [выполнение](../glossary.md#term-execution) остаётся закрытым
- **Дата:** 2026-07-24

## Контекст

ADR-042 ограничил обязательную проверку одной реализацией `QWake-FP`, а `QW-1`
реализовал чистое ядро состояний, действий, разрешений и квитанций. До разработки
`superset pipeline` требуется однозначно связать это общее ядро с одним конечным
частным случаем. Без такой фиксации реализация могла бы менять метод, горизонт,
состав ответа, признаки, аналитику, стоимость или базовые линии после появления
первых траекторий.

## Решение

### 1. Единственный обязательный частный случай

Замораживается только следующая [конфигурация](../glossary.md#term-configuration):

```text
method=fixedpred
eta=1
canonical_executor=stage2_baseline
architecture=lenet_classic
horizon_rule=registered_inference_steps
qwake_fp_generalization_claim=false
```

`Strict`, произвольный `eta`, другая [архитектура](../glossary.md#term-architecture) и обучаемый `online`-контроллер не
входят в обязательный `QW-2` контракт.

### 2. Момент решения и канонический суффикс

Снимок `S_t` материализуется после завершения свипа `t` и до начала свипа
`t+1`, включая `S_0` до первого свипа. Конечный горизонт равен зарегистрированным
`inference_steps` конкретной конфигурации:

```text
decision_epoch=after_S_t_before_sweep_t_plus_1
candidate_indices=t_in_[0,K_ref]
snapshot_zero=initialized_state_before_first_sweep
canonical_suffix=remaining_stage2_baseline_sweeps
```

`COMPLETE_SUFFIX` всегда завершает оставшийся `stage2_baseline` и остаётся
закрытым при ошибке резервным переходом.

### 3. Требуемый ответ и основной дефект

Требуемый относительно задачи ответ содержит ровно:

```text
named_parameter_gradients
endpoint_beliefs
endpoint_loss
```

Основной дефект наследуется из `EX-IF0`:

```text
r_Gamma(t)=max(
  max_abs/max_abs_limit,
  relative_l2/max_relative_l2_limit,
  (1-cosine)/(1-min_cosine)
)
structural_or_finite_failure=infinity
M_star(t)=1-r_Gamma(t)
sufficient(t)=M_star(t)>=0
```

Профиль допусков неизменяем:

```text
lane=rocm_float32
max_abs=1e-5
max_relative_l2=1e-3
min_cosine=0.999
zero_atol=1e-7
```

Минимальный достаточный префикс определяется только правилом полного суффикса:

```text
t_star=min{t: sufficient(j)=true for every j in [t,K_ref]}
```

### 4. Конечная ось наблюдения

Развёртываемая ось имеет ровно три накопительных уровня:

#### `A0`

Только структурные поля без чтения значений тензоров:

```text
snapshot_id
compute_step
reference_horizon_k_ref
remaining_sweeps
registered_layer_order
registered_block_order
acquired_analytic_ids
diagnostic_budget_remaining_ns
```

#### `A1`

`A0` плюс конечный набор дешёвых `device-side` редукций:

```text
global_prediction_error_l2_sq
global_state_delta_l2_sq
per_layer_prediction_error_l2_sq
per_layer_state_delta_l2_sq
per_layer_prediction_error_max_abs
per_layer_state_delta_max_abs
```

#### `A2`

`A1` плюс локальные редукции на детерминированных вложенных префиксах размером
`32`, `128` и `256`. Если тензор меньше префикса, используется весь тензор.
Индексы выбираются без возвращения ранжированием хешей от:

```text
contract_id, model_seed, batch_id, layer_id, tensor_role
```

Сохраняются `L2^2` и `max_abs` для `prediction_error`, `state_delta` и `belief`.

`O`, `t_star`, будущая `reference`-траектория и `M_star` не входят ни в один
`pre-action` уровень.

### 5. Конечный аналитический реестр

Разрешены ровно три заранее зарегистрированных аналитики:

```text
rosenbaum_wavefront_status_v1   exact         minimum=A0
residual_persistence_v1         heuristic     minimum=A1
cost_dominance_v1               conservative  minimum=A0
```

- `rosenbaum_wavefront_status_v1` является аналитическим положительным контролем
  известного порядка завершения компонентов;
- `residual_persistence_v1` является только диагностикой и `baseline`;
- `cost_dominance_v1` может отсечь заведомо доминируемое приобретение, но не
  доказывает достаточность.

Ни одна аналитика не имеет права самостоятельно выполнить
`ACCEPT_FRONTIER`. Положительное решение возможно только после замороженного `risk admission`, выбранного `offline` в C2.

### 6. Базовые линии

Заморожен закрытый реестр:

```text
B0 full canonical suffix
B1 fixed prefix
B2 registered prediction-error/residual threshold
B3 A0-only
B4 fixed A0->A1->A2 cascade
B5 fixed analytic registry
B6 frozen QWake-FP
B7 post-action `oracle` frontier
```

`B7` является только недоступной при развёртывании верхней границей `offline`.

### 7. Три `matched`-пары наблюдения

`Pre-freeze validation` содержит ровно:

```text
P0: B0 <-> B0+A0
P1: B0 <-> B0+A0+A1
P2: B0 <-> B0+A0+A1+A2
```

Внутри каждой пары должны совпасть `endpoint response`, `parameter gradients`,
`beliefs`, `loss`, последовательность переходов, конечное `RNG-state` и `snapshot identity`.
Отдельно измеряются `host/device time`, синхронизации, `D2H`, временная память и
`trace bytes` наблюдателя.

### 8. Отображение стоимости

`Raw edge measurement` сохраняет:

```text
host_time_ns
device_time_ns
synchronization_count
d2h_bytes
temporary_memory_bytes
trace_bytes
```

Каждый временной `edge` относится ровно к одной категории:

```text
compute_ns
observer_ns
diagnostic_ns
control_ns
fallback_ns
```

Основой является откалиброванное распределение `host critical path`. `Device time`
публикуется как отдельная измеренная величина и не прибавляется второй раз.
Память определяется максимумом временной памяти на воспроизведённом пути;
`D2H` и `trace` остаются отдельными компонентами вектора. Порядок отбора:

```text
`safety` -> coverage -> cost
```

### 9. Роли и квитанции

`QW-2` не создаёт новую `permission matrix`. Он побайтно наследует закрытые
`allowlists` и `receipt requirements` из `QW-1`. В частности, C2 остаётся строго
`offline` и не получает `EXECUTE_FIXEDPRED`, сбор наблюдений, новый `oracle` или
`confirmatory access`.

### 10. Машиночитаемая фиксация

Канонический контракт создаётся чистым модулем:

```text
src/torch2pc_thesis/stage3b_qwake_fp_spec.py
```

и запечатывается как:

```text
experiments/frozen/stage3b-qwake-fp-special-case-v1/contract.json
experiments/frozen/stage3b-qwake-fp-special-case-v1/SHA256SUMS
```

Тест требует полного совпадения `canonical JSON`, его SHA-256 и `Python-spec`.

## Граница выполнения

Эта ADR не разрешает [запуск](../glossary.md#term-run) `FixedPred`, сбор `A0/A1/A2`, `live`-аналитику,
создание `oracle` `labels`, `policy activation` или [доступ к тестовой выборке](../glossary.md#term-test-dataset-access).

```text
qwake_fp_special_case_contract_frozen=true
qwake_fp_special_case_contract_id=stage3b-qwake-fp-special-case-v1
qwake_fp_method=fixedpred
qwake_fp_eta=1
qwake_fp_canonical_executor=stage2_baseline
qwake_fp_architecture=lenet_classic
qwake_fp_horizon_rule=registered_inference_steps
qwake_fp_primary_defect=ex_if0_r_Gamma_full_suffix_stability
qwake_fp_observation_registry=A0,A1,A2
qwake_fp_analytic_registry=rosenbaum_wavefront_status_v1,residual_persistence_v1,cost_dominance_v1
qwake_fp_baseline_registry=B0,B1,B2,B3,B4,B5,B6,B7
qwake_fp_paired_validation=P0,P1,P2
qwake_fp_cost_time_categories_exclusive=true
qwake_fp_role_matrix_inherited_from_qw1=true
qwake_fp_scientific_execution_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
qwake_next_stage=QW-3
```

## Последствия

- `QW-3` может реализовать только замороженные `registries` и `mappings`;
- изменение любого поля требует нового `contract_id`, нового `digest` и отдельного
  решения до научного `image freeze`;
- отрицательный результат по `opportunity`, `recognizability`, `safety` или `net cost`
  остаётся допустимым;
- спецификация не утверждает переносимость за пределы данного FixedPred `special case`.

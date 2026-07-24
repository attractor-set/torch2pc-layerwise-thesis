# План ограниченной проверки `QWake-FP`

[English version](qwake-fp-experimental-plan_EN.md)

**Статус:** `docs-only` `plan` `freeze` по `ADR-042`; [выполнение](glossary.md#term-execution), сбор признаков,
создание `oracle`-меток, `calibration`, `confirmatory` `access` и `test` `split` закрыты.

## 1. Центральный объект

Общий `QWake-PC` задаёт классы состояния, действий, допуска, стоимости,
происхождения и `fallback`. Магистерская работа реализует и проверяет только
`QWake-FP` — одну детерминированную `shadow`-инстанциацию для исправленного
особого случая Розенбаума:

```text
algorithm=FixedPred
eta=1
canonical_executor=stage2_baseline
validation_mode=shadow_only
full_reference=depth_bounded_canonical_suffix
independent_unit=model_seed
```

Экспериментальные выводы относятся только к этой зарегистрированной
инстанциации. Общая переносимость `QWake-PC` не считается подтверждённой.


Такое ограничение не уменьшает проверяемость результата: оно связывает каждый
вывод с одной точно заданной реализацией и заранее известным полным эталоном.

## 2. Центральный вопрос

> Может ли замороженная `QWake-FP` по дешёвой `pre-action` информации безопасно
> распознавать `task-relative` достаточный частичный `FixedPred` `prefix` раньше
> полного `canonical` `suffix` и сохранять положительную сквозную экономию после
> учёта `observation`, `analytic`, `synchronization`, `control`, `trace` и `fallback` `cost`?

Вопрос раскладывается на четыре последовательных `gate`:

1. существуют ли `pre-terminal` достаточные состояния;
2. распознаются ли они по допустимым `pre-action` данным;
3. проходит ли `frozen` `admission` `safety` `limit`;
4. остаётся ли положительная `net` `saving`.

Без прохождения предыдущего `gate` последующая интерпретация запрещена.

## 3. Единый `superset` `image`

До научного выполнения реализуется один конечный `pipeline`, включающий:

- `canonical` `FixedPred` `executor`;
- `QWake` `state` `machine`;
- `A0 / A1 / A2` `collectors`;
- конечный `analytic` `registry`;
- `canonical` `suffix` и `post-action` `O`;
- `edge` `measurement` и `decision-cost` `mapping`;
- `opportunity` и `recognizability` `analysis`;
- `policy` `manifest` `interpreter`;
- `baselines` и `nested` `ablations`;
- `shadow` `confirmatory` и `replication` `evaluators`;
- `sealing` и `publication` `export`.

После `pre-freeze` `validation` фиксируются:

```text
SOURCE_COMMIT
SOURCE_TREE_HASH
IMAGE_DIGEST
TORCH2PC_COMMIT
CODE_MANIFEST_SHA256
OUTPUT_SCHEMA_VERSION
CAPABILITY_SCHEMA_VERSION
POLICY_SCHEMA_VERSION
```

Между `C1`, `C2`, `C3` и `R` `executable` `code` и зависимости не меняются.

## 4. `Permission` `model`

`Capability` присутствует в образе, но не исполняется без разрешения:

```text
capability_present != capability_permitted
```

Обязательный реестр включает:

```text
COLLECT_A0
COLLECT_A1
COLLECT_A2
RUN_ANALYTIC_EXACT
RUN_ANALYTIC_CONSERVATIVE
RUN_ANALYTIC_HEURISTIC
RUN_COST_DOMINANCE_CHECK
COMPUTE_CANONICAL_SUFFIX
COMPUTE_POST_ACTION_ORACLE
ACCESS_DESIGN_DATA
ACCESS_CALIBRATION_DATA
ACCESS_CONFIRMATORY_DATA
ACCESS_REPLICATION_DATA
RUN_OPPORTUNITY_ANALYSIS
RUN_RECOGNIZABILITY_ANALYSIS
SELECT_POLICY
FREEZE_POLICY
LOAD_FROZEN_POLICY
EXECUTE_SHADOW_POLICY
EVALUATE_CONFIRMATORY
EVALUATE_REPLICATION
SEAL_EVIDENCE
PUBLISH_RESULTS
```

Каждая `effectful` функция самостоятельно вызывает `permission` `check`. Выключенная
`capability` не регистрирует `hook`, не читает `tensor`, не выделяет память, не
синхронизирует устройство и не создаёт `output`.

`Manifest` не передаёт код. Он может выбрать только зарегистрированные `role`,
`capabilities` и `entrypoints`.

## 5. `Campaign` `roles`

### `C1_COLLECTION`

Разрешены `trajectory` `collection`, `A0/A1/A2`, зарегистрированная аналитика,
полный `suffix`, `post-action` `oracle`, `edge` `costs`, `opportunity` `analysis` и `sealing`.

Запрещены `policy` `selection`, `confirmatory` `access`, `shadow` `policy` `execution` и
`publication`.

Выходы:

- полный `trajectory` `benchmark`;
- `oracle` `sufficiency` `labels`;
- `remaining-suffix` `cost`;
- `opportunity` `map`;
- `sealed` `C1` `receipt`.

### `C2_CALIBRATION`

`C2` является строго `offline` стадией. Она читает только `sealed` `C1`
`trajectory` `artifacts`; исполнение модели или получение новых наблюдений в ней
не допускается.

Разрешены `ACCESS_SEALED_C1_ARTIFACTS`, `RUN_OFFLINE_REPLAY`,
`RUN_RECOGNIZABILITY_ANALYSIS`, `EVALUATE_BASELINES`, `SELECT_POLICY`,
`FREEZE_POLICY` и `SEAL_EVIDENCE`.

Запрещены `EXECUTE_FIXEDPRED`, `COLLECT_A0`, `COLLECT_A1`, `COLLECT_A2`,
`RUN_LIVE_ANALYTICS`, `COMPUTE_CANONICAL_SUFFIX`, `COMPUTE_NEW_ORACLE_LABELS`,
`ACCESS_CONFIRMATORY_DATA`, изменение `collector`/`oracle`/`cost` `mapping` и
`publication`.

`Offline replay` открывает только уже сохранённое поле очередного уровня или
аналитики, воспроизводит переход `policy` и прибавляет измеренную в `C1`
маргинальную стоимость. Он не создаёт новые `tensor` значения и не пересчитывает
`oracle`.

Выходы:

- `risk`/`coverage`/`cost` `frontier`;
- `nested` `representation` `ablations`;
- одна `frozen` `QWake-FP` `policy`;
- `POLICY_MANIFEST_SHA256`;
- `sealed` `C2` `receipt`.

### `C3_CONFIRMATORY`

Разрешены `untouched` `confirmatory` `partition`, загрузка `frozen` `policy`, `shadow`
`execution`, полный `suffix`, `post-action` `audit`, `confirmatory` `evaluation` и `sealing`.

Запрещены `selection`/`freeze` `policy`, изменение `thresholds`, признаков, `analytic`
`order`, `primary` `defect`, `baselines` и `cost` `mapping`.

Порядок результата:

```text
SAFETY -> COVERAGE -> NET_COST
```

### `R_REPLICATION`

Используются тот же `image` `digest`, `policy` `manifest`, `thresholds`, `analytic` `order` и
`cost` `mapping`. Изменяется только заранее зарегистрированная `replication`
`configuration`. Предпочтительный вариант — `MNIST` при той же архитектуре.
`Retuning` запрещён.

## 6. `Sealed` `receipt` `chain`

```text
C1 receipt -> разрешение C2
C2 policy-freeze receipt -> разрешение C3
C3 evidence receipt -> разрешение R и results synthesis
C3/R sealed evidence -> отдельный publication gate
```

Каждый `request` связывает `image` `digest`, `source` `identity`, `code` `manifest`, `role`,
`partition`, `seed` `set`, `policy` `hash` и `receipts` предыдущих стадий.

## 7. Этапы реализации

### `QW-0` — `scope` `freeze`

Зафиксировать `QWake-PC / QWake-FP`, специальный случай, роли `C1/C2/C3/R`,
единый `image` и `publication-strength` `package`. Только документация.

### `QW-1` — `pure` `QWake` `contract`

Реализовать без Torch2PC/GPU:

```text
FrontierState
ObservationSnapshot
AnalyticResult
FrontierAction
AdmissionProposal
AdmissionDecision
EdgeMeasurement
DecisionCost
OracleLabel
Provenance
Capability
CampaignRole
PermissionSet
ExecutionContext
```

`Gate`: `deterministic` `replay`, `fail-closed` `defaults`, `invalid-combination` `rejection`,
`property` `tests`.

### `QW-2` — `QWake-FP` `special-case` `contract`

Заморозить `executor`, `eta=1`, `architecture`, `horizon`, `snapshot` `boundaries`,
`response`, `primary` `defect`, `observation` `levels`, `analytic` `registry`, `cost` `schema`,
`baselines`, `roles` и `receipt` `requirements`.

Состояние: завершено в [ADR-043](decisions/ADR-043-stage3b-qwake-fp-special-case-contract.md)
и запечатанном `stage3b-qwake-fp-special-case-v1`. Контракт фиксирует точные
`A0/A1/A2`, три аналитики, `B0-B7`, `P0-P2` и недублирующее отображение стоимости;
выполнение остаётся закрытым, следующий этап — `QW-3`.

### `QW-3` — `superset` `pipeline` `implementation`

Состояние: обязательный `backend-neutral pipeline` реализован. Он включает
закрытый `component registry`, `effect-local planning`, неизменяемую
`trajectory schema`, точные `A0/A1/A2`, конечный `policy interpreter`, B0–B7 и
`nested ablations`, `cost mapping`, `opportunity/recognizability`,
`shadow/replication evaluation`, чистое `sealing` и
`rendered_not_published export`. Политика остаётся данными встроенного
интерпретатора; `arbitrary code/plugins` отсутствуют. Адаптеры
`Torch2PC/ROCm` не связаны, выполнение закрыто, следующий этап — `QW-4`.

```text
qwake_fp_superset_pipeline_implemented=true
qwake_fp_superset_pipeline_execution_open=false
qwake_fp_live_adapters_bound=false
qwake_fp_component_registry_closed=true
qwake_fp_offline_replay_implemented=true
qwake_fp_next_stage=QW-4
```

### `QW-4` — `pre-freeze` `validation`

Выполнить `static`/`unit`/`integration` `checks`, CPU/ROCm `smoke`, `permission` `matrix`,
`negative` `permission` `tests`, `deterministic` `replay`, `schema` `checks`,
`corrupt`/`missing` `manifest` `tests`, `receipt-chain` `tests` и `baseline` `replay`
`tests`.

Проверку наблюдения выполнить тремя `matched` парами над одним логическим `B0`
и отдельным `matched`-исполнением `reference` внутри каждой пары:

```text
P0: B0 <-> B0+A0
P1: B0 <-> B0+A0+A1
P2: B0 <-> B0+A0+A1+A2
```

Каждая пара проверяет `canonical-result`/`RNG`/переходную эквивалентность,
корректность наблюдения и измеряет накопленную стоимость. Дополнительно
проверяются вложенность `A0` и `A1`, невыполнение закрытых `capabilities`,
изоляция `post-action` `oracle` и `non-interference` зарегистрированной аналитики.

### `QW-5` — `single` `image` `freeze`

Зафиксировать одну `code`/`environment` `identity`. Любая существенная ошибка после
`freeze` требует нового `digest` и новой `protocol` `version`; старые `evidence` не
переписываются.

### `QW-6` — `C1` `collection` `and` `opportunity`

Собрать полные `design`/`calibration` `trajectories`, достаточные для последующего
`offline C2`: все `snapshot`, `A0/A1/A2`, зарегистрированную аналитику,
маргинальные `edge` `costs`, канонический суффикс и `post-action` `oracle` `labels`.
Проверить:

```text
exists_preterminal_sufficient_state
potential_avoided_cost_exceeds_lower_bound_of_control_overhead
```

При отрицательном `gate` дальнейшая `policy` `selection` не обязательна; результат
оформляется как `bounded` `negative` `finding`.

### `QW-7` — `C2` `offline recognizability`, `deterministic replay` и `policy` `freeze`

Не выполняя новых запусков `FixedPred`, воспроизвести на `sealed C1 artifacts`:

```text
A0
A0+A1
A0+A1+A2
A0+A1+A2+analytics
```

Выбирать простейшую безопасную почти недоминируемую `policy`. `Safety` имеет
лексикографический приоритет над `coverage` и `cost`.

### `QW-8` — `C3` `untouched` `confirmatory` `shadow` `evaluation`

Основная единица — `model_seed`. `Snapshot-level` строки используются только как
вложенная диагностика. После открытия `partition` `policy` и `analysis` `contract` не
меняются.

Допустимые классы результата:

```text
SAFE_AND_BENEFICIAL
SAFE_BUT_NOT_BENEFICIAL
UNSAFE
NO_NONTRIVIAL_COVERAGE
INSUFFICIENT_EVIDENCE
```

### `QW-9` — `replication` `without` `retuning`

Применить ту же `frozen` `policy` к заранее выбранной дополнительной конфигурации.
Успех усиливает внешнюю валидность; `failure` фиксирует границу переноса.

### `QW-10` — `synthesis` `and` `publication` `gate`

Объединить результаты существования, `recognizability`, `safety`, `coverage`, `cost`,
`ablations` и `replication`. `Publication` выполняется только отдельным `bounded`
решением после `sealing`.

## 8. `Baselines` и `ablations`

Обязательные `baselines` заранее встроены в образ:

```text
B0 full canonical suffix
B1 fixed prefix
B2 residual/prediction-error threshold
B3 A0-only
B4 fixed A0->A1->A2 cascade
B5 fixed analytic registry
B6 frozen QWake-FP
B7 post-action oracle frontier
```

`B7` является только `offline` `upper` `bound`. После `confirmatory` `access` новый
`baseline` не добавляется.

Обязательные `ablations` выключают по одному:

- `A1`;
- `A2`;
- `analytic` `steps`;
- `adaptive` `ordering`;
- `cost-dominance` `checks`.

## 9. Публикационная сила

Минимальный `publication-strength` пакет включает:

- простые сильные `baselines`;
- `untouched` `confirmatory` `seeds`;
- exact `one-sided` `seed-level` `safety` `bounds`;
- одну `replication` без `retuning`;
- полный `accounting` `observer`/`control` `overhead`;
- открываемый `trajectory` `benchmark` с `provenance`;
- положительный или заранее допустимый отрицательный результат.

## 10. Вне обязательного `scope`

```text
Strict
arbitrary eta
recursive multiscale control
spatial active sweeps
learned policy
contextual bandit
online exploration
cross-algorithm transfer
plugin or arbitrary policy DSL
QWake-SPC
```

Эти направления не блокируют завершение магистерской работы и не входят в
единый обязательный `image`.

## 11. Текущая закрытая граница

```text
qwake_fp_scope_freeze_complete=true
qwake_fp_execution_permitted=false
single_immutable_superset_image_frozen=false
c2_execution_mode=offline_only
c2_input_artifacts=sealed_c1_trajectory_dataset
c2_live_fixedpred_execution_permitted=false
c2_new_observation_collection_permitted=false
c2_new_oracle_generation_permitted=false
c2_policy_selection_from_frozen_artifacts_only=true
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

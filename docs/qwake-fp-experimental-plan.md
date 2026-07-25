# План ограниченной проверки `QWake-FP`

[English version](qwake-fp-experimental-plan_EN.md)

**Статус:** активный план после `QW-4B-DOC-R1`; [выполнение](glossary.md#term-execution),
создание новых меток оракула, доступ к подтверждающей и тестовой выборкам и
активация политики закрыты.

## 1. Центральный объект

`QWake-FP` — ограниченная теневая инстанциация `QWake-PC` для зарегистрированного
случая:

```text
algorithm=FixedPred
eta=1
canonical_executor=stage2_baseline
architecture=lenet_classic
validation_mode=shadow_only
independent_unit=model_seed
```

Общая переносимость `QWake-PC` не считается подтверждённой.

## 2. Исследовательская модель

Для действия `a` в состоянии `s` отдельно рассматриваются `R(a,s)`, `M(a)`,
`Γ(a,s)` и `C(a,s)`. Нужный ответ не определяет единственный механизм или
единственную стоимость. Поэтому сравнение способов разделяет эквивалентность
по `R` и эквивалентность по `C`.

Допустимыми считаются только действия, для которых зарегистрированный
[regret решения](glossary.md#term-decision-regret) не превышает `ε`. Среди них
выбирается действие с минимальной зарегистрированной стоимостью либо применяется
заранее зафиксированное правило Парето.

## 3. Две границы разработки

### Базовая проверка `QW-4B`

Она подтверждает, что уровни наблюдения `A0/A1/A2` не вмешиваются в исходный
`FixedPred`, корректно измеряются на CPU и ROCm и могут быть запечатаны в одном
инженерном отчёте. Базовая проверка не содержит `LOCAL_COMPUTE`.

Три сопоставленные пары остаются неизменными:

```text
P0: B0 <-> B0+A0
P1: B0 <-> B0+A0+A1
P2: B0 <-> B0+A0+A1+A2
```

### Расширение `QW-LC`

Оно добавляет только после запечатанного базового отчёта:

```text
LOCAL_COMPUTE
├── LOCAL_SWEEP
└── ANALYTIC_COMPLETION
```

Первый аналитический [кандидат](glossary.md#term-candidate) ограничен
`fixedpred_eta1_wavefront_completion_v1` и не обобщается на `Strict`,
произвольные значения `eta` или произвольные вычислительные графы.

## 4. Модель разрешений

Наличие возможности в образе не означает разрешение на её использование:

```text
capability_present != capability_permitted
```

Каждая функция с внешним эффектом обязана самостоятельно проверять разрешение.
Отключённая возможность не регистрирует перехватчик, не читает тензор, не
выделяет память устройства, не синхронизирует устройство и не создаёт выходной
файл.

Обязательные классы разрешений:

```text
COLLECT_A0
COLLECT_A1
COLLECT_A2
COMPUTE_CANONICAL_SUFFIX
COMPUTE_POST_ACTION_ORACLE
EXECUTE_LOCAL_SWEEP
EXECUTE_ANALYTIC_COMPLETION
RUN_COST_DOMINANCE_CHECK
ACCESS_DESIGN_DATA
ACCESS_CALIBRATION_DATA
ACCESS_CONFIRMATORY_DATA
ACCESS_REPLICATION_DATA
SELECT_POLICY
FREEZE_POLICY
EXECUTE_SHADOW_POLICY
SEAL_EVIDENCE
PUBLISH_RESULTS
```

## 5. Роли кампании

### `C1`

Собирает полные траектории, `A0/A1/A2`, зарегистрированную аналитику, стоимость
переходов, канонический суффикс и метки после действия. Выбор политики и доступ к
подтверждающей выборке запрещены.

### `C2`

Работает только офлайн над запечатанными материалами `C1`. Новое выполнение
модели, новые тензоры и новые метки запрещены. Выход — одна зафиксированная
теневая политика либо ограниченный отрицательный результат.

```text
c2_execution_mode=offline_only
c2_input_artifacts=sealed_c1_trajectory_dataset
c2_live_fixedpred_execution_permitted=false
c2_new_observation_collection_permitted=false
c2_new_oracle_generation_permitted=false
c2_policy_selection_from_frozen_artifacts_only=true
C2_ALLOWED=ACCESS_SEALED_C1_ARTIFACTS,RUN_OFFLINE_REPLAY
C2_FORBIDDEN=EXECUTE_FIXEDPRED,COMPUTE_NEW_ORACLE_LABELS
```

### `C3`

Использует нетронутые случайные начальные значения, загружает зафиксированную
политику и всегда завершает канонический суффикс для проверки после действия.
Порядок оценки: безопасность, покрытие, чистая стоимость.

### `R`

Повторяет `C3` без перенастройки. Изменяется только заранее зарегистрированная
[конфигурация](glossary.md#term-configuration) воспроизведения.

## 6. Цепочка квитанций

```text
QW-4B-F-v2 receipt -> QW-4B-E-v2
QW-4B-E-v2 report -> QW-LC0
QW-LC4-E report -> QW-5
QW-5 image receipt -> C1
C1 receipt -> C2
C2 policy receipt -> C3
C3 evidence receipt -> R
C3/R evidence -> publication gate
```

Каждый следующий запрос связывает фиксацию версии исходного кода, хеш образа, роль,
раздел данных, набор случайных начальных значений и предыдущие квитанции.

## 7. Последовательность реализации

### `QW-0`–`QW-4B-I`

Исторически завершены фиксация области, чистый контракт, специальный случай,
нейтральный к вычислительной основе конвейер, запрос `QW-4A` и реализация
базовой проверки `QW-4B-I`.

```text
historical_sequence=QW-2->QW-3->QW-4A->QW-4B-I
qwake_fp_special_case_contract_id=stage3b-qwake-fp-special-case-v1
qwake_fp_superset_pipeline_implemented=true
qwake_fp_superset_pipeline_execution_open=false
qwake_fp_live_adapters_bound=false
qwake_fp_component_registry_closed=true
qwake_fp_offline_replay_implemented=true
```

### `QW-4B-DOC-R1`

Полностью синхронизировать активную документацию, рабочие журналы,
машиночитаемый контракт и проверки границ. Вывести старое разрешение из
обращения. После слияния обязателен новый образ.

### Новый базовый образ

Собрать неизменяемый образ из фиксации версии после слияния `QW-4B-DOC-R1`. Образ всё ещё
не содержит реализацию `LOCAL_COMPUTE`; он нужен для повторной чистой базовой
проверки.

### `QW-4B-F-v2`

Заново зафиксировать предварительную проверку, квитанцию статических проверок,
точные ячейки CPU/ROCm, новый хеш образа, новую фиксацию версии, каталог результата и
одноразовое разрешение.

### `QW-4B-E-v2`

Один раз выполнить шесть базовых ячеек и запечатать двухлинейный инженерный
отчёт. При неуспехе `QW-LC0` не открывается.

### `QW-LC0`

Зафиксировать семантику `R/M/Γ/C`, область кандидата, границы утверждений и
запрет универсального обобщения.

### `QW-LC1`

Зафиксировать конечный ответ и обязательные наблюдаемые величины, которые должен
воспроизводить каждый механизм.

### `QW-LC2`

Зафиксировать измеряемую `Γ` и недублирующее отображение в `C`.

### `QW-LC3`

Задать сопоставленную теневую проверку явного прохода и аналитического
завершения с общим состоянием, восстановлением генераторов и полным резервным
суффиксом.

### `QW-LC4-I`

Реализовать ограниченный кандидат без открытия выполнения.

### `QW-LC4-F`

Собрать новый образ расширения и выпустить отдельное одноразовое разрешение.

### `QW-LC4-E`

Выполнить инженерную проверку расширения и запечатать отчёт. Только успешный
отчёт открывает `QW-5`.

### `QW-5`

Зафиксировать единственный научный образ для `C1/C2/C3/R`. После этой точки код
и зависимости не меняются.

### `C1` → `C2` → `C3` → `R`

Последовательно выполнить сбор, офлайн-отбор, подтверждающую теневую оценку и
воспроизведение без перенастройки.

## 8. Базовые сравнения и абляции

Минимальный набор включает полный канонический суффикс, `LOCAL_SWEEP`,
`ANALYTIC_COMPLETION`, безопасный точный резервный путь, вложенные представления
`A0`, `A0+A1`, `A0+A1+A2` и зарегистрированную аналитику. Стоимость наблюдения,
управления и резервного перехода учитывается отдельно.

## 9. Сила публикационного вывода

Положительный вывод требует одновременно ограничения `Regret_R`,
отсутствия опасных пропусков, ненулевого покрытия и положительной чистой
экономии. Любой ранний провал не компенсируется поздним выигрышем. Отрицательный
результат сохраняется без изменения критериев.

## 10. Вне обязательной области

Не входят универсальный символьный решатель, произвольные архитектуры,
произвольные значения `eta`, активное управление до теневой проверки,
перенастройка на подтверждающей выборке и использование тестовой выборки для
выбора механизма или политики.

## 11. Текущая закрытая граница

```text
qwake_documentation_refactor_complete=true
qwake_old_runtime_authorization_retired=true
qwake_old_runtime_authorization_reuse_permitted=false
qwake_new_image_required=true
qwake_new_runtime_preflight_captured=false
qwake_new_runtime_authorization_issued=false
qwake_runtime_execution_performed=false
qwake_runtime_validation_performed=false
qwake_engineering_evidence_present=false
qwake_fp_execution_permitted=false
qwake_local_compute_contract_frozen=true
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
qwake_scientific_image_freeze_permitted=false
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
publication_permitted=false
full_stage3b_campaign_complete=false
```

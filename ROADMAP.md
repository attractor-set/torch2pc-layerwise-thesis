# Дорожная карта

[English version](ROADMAP_EN.md)

Дорожная карта отделяет завершённые этапы от разрешённой и заблокированной
работы. Каждый переход требует проверенных артефактов, сохранения границ
утверждений и отдельного решения о допуске.

## Этапы 1–10 — завершены

Завершены инфраструктура и пилот, Stage 1/2, Stage 3A, доказательные материалы
Stage 3B B0 и статистический и инженерный анализ B0. Тестовая выборка
оставалась закрытой.

## Этап 11 — Scenario A и исходная теория — завершён

`ADR-012` закрепил PC-TREF Balanced Core, PC-CATM и Scenario A. `ECZ` имеет
единственное значение `Error-Cancellation Zone`; B0 остаётся неизменяемой
базовой линией.

## Этап 12 — проверки валидности и `SI-MA0` — завершён

Завершены проверки shortcut/equivalence, невмешательства наблюдателя,
детерминированные механизмные контроли и `SI-MA0`. Проверки `REC`, `OBS`,
`VER` и `CMP` прошли, `COST` не прошёл; общий отрицательный итог сохранён.

## Этап 13 — `SI-MA1` — завершён

Завершены предварительная регистрация, реализация, подтверждающее выполнение
и итоговое решение `SI-MA1`. На десяти `model_seed` и 180 сопоставленных
блоках получено `CAL-COST-MA1=true`, `SI-MA1=pass`. Результат `SI-MA0`
не изменён; стоимость будущего оценивателя `ECZ` исключена.

## Этап 14 — теоретическая фиксация перед B1/B2 — завершён

Операциональная семантика PC-TREF/PC-CATM, regret, контракты норм,
`precision-masked zero`, вектор стоимости и разделение затрат опубликованы
под `ADR-013`.

## Этап 15 — предварительная регистрация B1/B2 — завершён

Зафиксированы B1 `isolated_layer_vjp`, B2 `composite_vjp`, общий обзор и
`ADR-014`. Публикационный тег: `stage3b-b1-b2-prereg-v1`. Варианты B2
`block`/`chunk` не входят в этот контракт и требуют отдельной предварительной
регистрации.

## Этап 16 — точные кандидаты и [сопоставленное профилирование](docs/glossary.md#term-matched-profiling) — анализ опубликован, receipt зафиксирован

Завершено:

- B1 реализован и запечатан как confirmatory `EQ-B1` на 120/120 парах;
- B2 реализован и прошёл engineering smoke на 12/12 тройках и 24/24
  сравнениях;
- реализован candidate-aware matched-profiling runner;
- зафиксировано fail-closed требование confirmatory B2 перед production launch;
- предварительно зарегистрирован confirmatory B2 на 120 троек и 240 сравнений;
- выполнен и запечатан confirmatory B2: 120/120 троек, 240/240 сравнений, `EQ-B2-CONFIRMATORY=pass`, derived `EQ-B2`; evidence сохранён в `stage3b-b2-confirmatory-63885e5-v1`.

Текущая граница:

```text
scientific_admission=open
candidate_aware_runner=complete
b2_confirmatory_decision=pass_sealed
b2_confirmatory_request_frozen=true
b2_confirmatory_admission=present
matched_profiling_request_refrozen=true
matched_profiling_request_refresh_required=false
matched_profiling_execution_open=false
matched_profiling_execution_complete=true
matched_profiling_runtime_validation=valid
matched_profiling_evidence=sealed
matched_profiling_analysis_protocol_frozen=true
matched_profiling_analysis_implementation_complete=true
matched_profiling_analysis_preexecution_hardening=complete
matched_profiling_analysis_execution_request_frozen=true
matched_profiling_analysis_runtime_preflight_implementation=complete
matched_profiling_analysis_runtime_preflight_frozen=true
matched_profiling_analysis_execution_authorization_present=true
matched_profiling_analysis_synthetic_validation=pass
matched_profiling_analysis_execution_open=false
matched_profiling_analysis_execution_complete=true
matched_profiling_analysis_results_present=true
matched_profiling_analysis_output_audited=true
matched_profiling_analysis_output_seal_frozen=true
matched_profiling_analysis_output_evidence=true
matched_profiling_analysis_publication_gate_frozen=true
matched_profiling_analysis_publication_action_complete=true
matched_profiling_analysis_publication_receipt_frozen=true
matched_profiling_analysis_open=false
runtime_authorization=issued_consumed
measurements_allowed=false
results_publication_permitted=true
release_draft_required=false
release_publication_permitted=true
release_publication_complete=true
ex_if0_protocol_frozen=true
ex_if0_opened=true
ex_if0_complete=true
exact_implementation_frozen=true
exact_implementation_candidate=stage2_baseline
minimum_sufficient_sweep_rule_frozen=true
ex_if0_execution_permitted=false
oracle_label_generation_open=false
feature_collection_permitted=false
a11_off0_execution_open=false
recursive_aggregate_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

Новый версионированный `v2` request/manifest freeze со ссылками на sealed
admissions B1 и B2 завершён. Immutable image, ROCm/float32 preflight,
authorization и dry-run прошли. Все 288 ячеек и 96 matched blocks выполнены без
failures и retries, runtime validation прошла, а compact evidence package
запечатан и перенесён в репозиторий.

Execution request `v1`, runtime preflight и authorization были зафиксированы до
вычисления. Единственная read-only попытка завершена на проверенном `main`;
18-файловый output, receipt и независимый audit сохранены без повторного запуска.
Внешний seal связывает эти артефакты и переводит output в repository evidence,
не изменяя generated metadata.

Этап 16 завершён: fail-closed publication action успешно выполнен, а точный
remote receipt/status зафиксирован без повторного анализа. Утверждения о
превосходстве, политика и test split остаются закрытыми. Отрицательные и
смешанные результаты сохранены.

## Этап 17

<!-- BEGIN STAGE3B-DUS-FUTURE-POLICY-COMPATIBILITY -->
### Совместимая граница будущей политики

`EX-IF0` сохраняет canonical exact reference и fail-closed fallback.
`A11-OFF0` остаётся policy-neutral этапом snapshot и oracle collection.
`A11-OFF1` может открыться только после информативных gates; его predictor
оценивается исключительно в shadow mode и не управляет execution.
<!-- END STAGE3B-DUS-FUTURE-POLICY-COMPATIBILITY -->
 — `EX-IF0` и oracle-граница рекурсивных агрегатов

Design freeze `EX-IF0 v1` завершён: `stage2_baseline` выбран как канонический
точный reference и fail-closed fallback для `FixedPred` и `Strict`. Decision
epoch, полный конфигурационный reference horizon, task-relative endpoint,
`rocm_float32` threshold profile и правило полного suffix для минимального
устойчиво достаточного свипа зафиксированы. Выполнение и создание меток не
открыты.

Следующий отдельный контракт должен до создания меток зафиксировать конкретную
пространственную иерархию и snapshot-ветвление `A11-OFF0`. Temporal baseline
сохраняет нейтральные ветви `stop`, `native_one` и `exact_one`; в `v1` две
one-step ветви являются identity-control выбранного `stage2_baseline`. Затем из
идентичного `snapshot` проверяются заранее заданные вложенные агрегаты минимум
на двух масштабах: слои внутри блока и блоки внутри сети. Для каждого кандидата
сохраняются `exact-reference regret`, oracle-запас `M^*`, полный вектор
стоимости и происхождение.

Решения этапа:

- `E2`: существует ли более дешёвый достаточный частичный агрегат;
- `E3`: зависит ли oracle-оптимальный агрегат от состояния;
- `E5`: повторяется ли одна нормативная семантика на двух масштабах;
- `H0`: занята ли окрестность границы достаточности;
- `P0`: существует ли диагностическая возможность без `pre-action` leakage.

Предиктор, температура, гистерезис и `QWake-PC` на этом этапе не управляют
выполнением. Независимая единица — `model_seed`; test split закрыт.


## Этап 18 — `DUS-0` и `DUS-1`: фиксация и рефакторинг

ADR-040 добавляет интегрированную модель фронтира поверх неизменного ADR-039.
Обязательная ось наблюдения — `A0 -> A1 -> A2`, а `O` остаётся post-action
oracle. Теневой алфавит действий — `ACCEPT_FRONTIER`, `ADVANCE_FRONTIER`,
`COMPLETE_SUFFIX`; `controls_execution=false`.

ADR-039 фиксирует `FixedPred`, `stage2_baseline`, oracle `EX-IF0`,
[wavefront-контроль Rosenbaum](docs/glossary.md#term-rosenbaum-wavefront-control)
и [семантику решений
D/U/S](docs/glossary.md#term-dus-decision-semantics).

Сначала выполняются только:

- выделение нового namespace `stage3b_sufficiency`;
- разделение oracle, `pre-action` features, policy и cost accounting;
- схемы, pure types и synthetic tests;
- deterministic analytic registry;
- проверка невмешательства и provenance.

Научное выполнение на этом этапе закрыто.

## Этап 19 — `DUS-2` и `DUS-3`: положительный контроль и контракт

Проверить Rosenbaum special case как аналитический component-completion
positive control. Затем отдельным контрактом зафиксировать `A11-OFF0`,
snapshot schema, temporal prefixes, optional spatial aggregates, endpoint,
cost fields, seeds и no-test boundary.

## Этап 20 — `DUS-4`–`DUS-7`: collector и oracle

Реализовать policy-neutral collector, затем отдельно зафиксировать runtime
preflight и authorization. После разрешённого сбора:

- сохранить `pre-action` representations;
- выполнить полный canonical suffix;
- вычислить `M^*(t)` и `t^*`;
- измерить полный cost vector;
- сохранить provenance;
- до сравнительного анализа зафиксировать estimands, thresholds, risk-control
  procedure и negative-result rules.

Policy не управляет execution.

## Этап 21 — `DUS-8` и `DUS-9`: opportunity и представления

Сначала определить, существует ли ранний достаточный префикс, зависит ли он от
состояния, наблюдаем ли он дёшево и экономически допустима ли диагностика.

Затем сравнить вложенные представления в порядке:

```text
dangerous DONE
safe coverage
UNKNOWN burden
diagnostic cost
context stability
```

При отсутствии state dependence использовать статический вариант.

## Этап 22 — `DUS-10`: deterministic shadow replay

Сравнить fixed cascade, cheapest-first, greedy quality,
greedy quality/cost, all metrics и offline oracle sequence.

```text
controls_execution=false
```

Greedy policy не считается глобально оптимальной.

## Этап 23 — условная итоговая фиксация

Confirmatory evaluation открывается только при ненулевой safe coverage,
допустимом dangerous-DONE risk, observer non-interference, cost feasibility и
устойчивости по `model_seed`.

Только после отдельной final freeze разрешается однократная тестовая оценка.

## Этап 24 — диссертация и статья

Объединить Stage 1/2, Stage 3A, B0, `SI-MA0`, `SI-MA1`, B1/B2, `EX-IF0` и
результаты D/U/S. Невыполненные spatial, learned и active extensions обозначить
как будущую работу.

## Граница после магистерской работы — перспективная PhD-линия

После завершения текущего критического пути возможна отдельная программа
`QWake-SPC`: переход от
[спайкоподобной управляющей динамики](docs/glossary.md#term-spike-like-control-dynamics)
QWake-PC к нативным spikes, spike-native переносу ошибок, локальному обучению и
нейроморфной проверке. Эта программа не является этапом 21, не открывает
выполнение и не изменяет критерии завершения магистерской работы.

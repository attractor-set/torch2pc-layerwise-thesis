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

## Этап 17 — `EX-IF0` и текущий design boundary — завершён

`stage2_baseline` зафиксирован как canonical exact reference и fail-closed
fallback. Decision epoch, task-relative endpoint, oracle margin и правило
полного suffix для минимального устойчиво достаточного sweep заморожены.
Выполнение и создание oracle labels не открыты.

ADR-039–ADR-041 задают D/U/S и интегрированный temporal frontier. ADR-042
дополнительно ограничивает обязательную проверку одной реализацией
[QWake-FP](docs/glossary.md#term-qwake-fp) на исправленном Rosenbaum FixedPred
при `eta=1` и вводит один immutable permission-gated image.

Историческая policy-очередь после `EX-IF0` сохраняется как provenance, но не
как текущий mandatory critical path: `A11-OFF0` обозначает offline opportunity
и recognizability analysis, `A11-OFF1` — заморозку выбранного `predictor`, после
чего допускается только `shadow`-оценка. ADR-042 переносит эти работы в роли
`C1/C2/C3`, не открывая execution gates.

## Этап 18 — `QW-0`: scope freeze — текущий docs-only этап

Зафиксировать:

- различие общей спецификации `QWake-PC` и конкретной `QWake-FP`;
- corrected Rosenbaum FixedPred special case;
- роли `C1_COLLECTION / C2_CALIBRATION / C3_CONFIRMATORY / R_REPLICATION`;
- один конечный superset image;
- permission checks на границах эффектов;
- frozen policy как data manifest;
- publication-strength baselines, untouched seeds, ablations, replication и
  trajectory benchmark.

Научное выполнение, labels, features, calibration и test access закрыты.

## Этап 19 — `QW-1`: pure QWake contract

Без Torch2PC и GPU реализовать pure types `FrontierState`, observations,
analytics, actions, admission, costs, oracle labels и provenance, а также
`Capability`, [роль кампании](docs/glossary.md#term-campaign-role),
`PermissionSet` и `ExecutionContext`.

Gate: fail-closed defaults, deterministic replay, property tests и rejection
всех несовместимых permission combinations.

Состояние: `QW-1` реализован как pure Python contract без Torch2PC/GPU;
по умолчанию все permissions запрещены, роль/receipt/digest bindings и
детерминированные переходы покрыты exhaustive unit/property guards.
Научное выполнение не открыто. Следующий обязательный этап — `QW-2`.

## Этап 20 — `QW-2`: контракт особого случая `QWake-FP`

Заморозить `FixedPred`, `eta=1`, `stage2_baseline`, architecture, horizon,
snapshot boundaries, task-relative response, primary defect, `A0/A1/A2`,
analytic registry, cost schema, baselines, role matrix и receipt requirements.

Состояние: `QW-2` завершён. `ADR-043`, pure Python spec и sealed
`stage3b-qwake-fp-special-case-v1/contract.json` фиксируют `lenet_classic`,
EX-IF0 defect, точные registries `A0/A1/A2`, analytics, B0–B7 и P0–P2, а
permission/receipt mapping наследуется из `QW-1`. Выполнение закрыто.
Следующий обязательный этап — `QW-3`.

## Этап 21 — `QW-3`: реализация superset pipeline

Состояние: backend-neutral обязательный контур реализован в
`stage3b_qwake_fp_pipeline.py`. Он включает закрытый component registry,
effect-local planning, exact `A0/A1/A2` trajectory schema, finite policy
interpreter, B0–B7 и nested-ablation replay, cost mapping, opportunity и
recognizability, shadow/replication evaluation, pure sealing и
`rendered_not_published` export. Manifest не загружает произвольный код и может
активировать только встроенные capabilities.

Live Torch2PC/ROCm adapters не связаны, поэтому выполнение остаётся закрытым.
Следующий обязательный этап — `QW-4`.

```text
qwake_fp_superset_pipeline_implemented=true
qwake_fp_superset_pipeline_execution_open=false
qwake_fp_live_adapters_bound=false
qwake_fp_component_registry_closed=true
qwake_fp_offline_replay_implemented=true
qwake_fp_next_stage=QW-4
```

## Этап 22 — `QW-4B-DOC-R1`: рефакторинг активной документации

Состояние: завершено. Старый кандидат разрешения выведен из обращения до выполнения, активные документы переведены к единой модели `R/M/Γ/C`, семейству `LOCAL_COMPUTE` и одной последовательности этапов. Рефакторинг слит в `main` commit `e413bb1e13cee42f702512e499f994e90df21e45`.

## Этап 23 — `QW-4B-F-v2`: повторная заморозка базовой проверки

Состояние: завершено без выполнения модели. Новый неизменяемый образ, Torch2PC, предварительная проверка, квитанция 17 статических проверок, шесть ячеек `CPU/ROCm × P0/P1/P2`, отсутствующий каталог результата и одна разрешённая попытка зафиксированы в новом пакете.

```text
source_commit=e413bb1e13cee42f702512e499f994e90df21e45
image_digest=sha256:bd91fab26df5f91a3aba90b8cad38badccab3a1a7bfb20efe4126a88a13236c4
preflight_sha256=sha256:79ead4a0e757272c788acd90700d61c0e5a0509fe64168f83f47dc0963ce4d00
authorization_sha256=sha256:d22063efa0c458c2498577139fa322b952081d8356cd1a6511f25188b12206b6
P0: B0 <-> B0+A0
P1: B0 <-> B0+A0+A1
P2: B0 <-> B0+A0+A1+A2
runtime_execution_performed=false
engineering_evidence_present=false
next_slice=QW-4B-E-v2
```

Одноразовая попытка не использована. Следующим отдельным этапом остаётся только `QW-4B-E-v2`.

## Этап 24 — `QW-4B-E-v2`: запечатанный базовый отчёт

Состояние: завершено. Repository seal commit
`26bc0ef635e13dba719d3356fe17382f0037d1df` слит в `main`
`4f23b752a40ae05de9fc7ee49c9962c44083b71d` и повторно проверен. Единственная попытка окончательно
использована; повтор запрещён.

```text
runner_status=0
authorized_cell_count=6
cpu_lane_passed=true
rocm_lane_passed=true
runtime_execution_performed=true
engineering_evidence_present=true
image_freeze_eligible=true
scientific_evidence=false
publication_permitted=false
repository_evidence_sealed=true
post_merge_verification_passed=true
qw_lc0_transition_permitted=true
qw_lc0_open=true
qw_lc0_semantics_scope_frozen=false
next_slice=QW-LC0
post_lc0_next_slice=QW-LC1
```

Исходная ошибка wrapper, два неудачных recovery-аудита и успешный recovery-v3
сохраняются вместе с точным шестифайловым output. `QW-LC0` не исполняет модель:
он должен отдельно зафиксировать только семантику и область расширения.

## Этапы 25–31 — расширение `QW-LC`

```text
QW-LC0  semantics and scope freeze
QW-LC1  required-response freeze
QW-LC2  resource-trajectory and cost freeze
QW-LC3  matched-validation freeze
QW-LC4-I bounded implementation
QW-LC4-F extension image and authorization freeze
QW-LC4-E sealed engineering execution
```

Расширение сравнивает `LOCAL_SWEEP` и `ANALYTIC_COMPLETION` только внутри
зарегистрированной области. Оно не открывает научную кампанию и не изменяет
старые доказательные материалы.

## Этап 32 — `QW-5`: единая заморозка научного образа

После успешных базового и расширенного инженерных отчётов зафиксировать один
commit, один digest образа, `Torch2PC`, манифест кода и версии схем. Между
`C1/C2/C3/R` код и зависимости не меняются.

## Этап 33 — `C1`: сбор и проверка возможности

Собрать полные траектории, `A0/A1/A2`, зарегистрированную аналитику, стоимость
переходов, канонический суффикс и метки после действия. Проверить существование
достаточных промежуточных состояний и потенциальную экономию сверх накладных
расходов управления.

## Этап 34 — `C2`: офлайн-отбор и фиксация политики

Использовать только запечатанные материалы `C1`. Новое выполнение модели и новые
метки запрещены. Выбрать простейшую безопасную почти недоминируемую политику или
зафиксировать отрицательный результат.

## Этап 35 — `C3`: подтверждающая теневая оценка

На нетронутых случайных начальных значениях загрузить зафиксированную политику,
выполнить теневые предложения и всегда завершить канонический суффикс для
проверки после действия.

## Этап 36 — `R`: воспроизведение без перенастройки

Повторить подтверждающую оценку с заранее зарегистрированной конфигурацией,
сохраняя образ, политику, пороги и отображение стоимости.

## Этап 37 — синтез и публикационный барьер

Свести безопасность, покрытие, полную стоимость, ограничения переносимости и
отрицательные результаты. Публикация требует отдельной квитанции и не открывает
новое выполнение.

## Граница после магистерской работы — перспективная PhD-линия

После завершения текущего критического пути возможна отдельная программа
`QWake-SPC`: переход от
[спайкоподобной управляющей динамики](docs/glossary.md#term-spike-like-control-dynamics)
QWake-PC к нативным spikes, spike-native переносу ошибок, локальному обучению и
нейроморфной проверке. Эта программа не является этапом 21, не открывает
выполнение и не изменяет критерии завершения магистерской работы.


## Этап 25 — `QW-LC0`: фиксация семантики и области

Состояние: материализовано в ветке. Контракт `stage3b-qwake-lc0-semantics-scope-v1` фиксирует
разделение `R/M/Γ/C`, семейство `LOCAL_COMPUTE`, область первого кандидата и
границу утверждений. До слияния переход к `QW-LC1` не разрешён. Реализация,
выполнение и научная кампания закрыты.

```text
qwake_qw_lc0_semantics_scope_frozen=true
qwake_qw_lc1_transition_permitted=false
qwake_qw_lc1_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
next_slice=QW-LC0-repository-freeze
post_merge_next_slice=QW-LC1
```

## Этап 25 — `QW-LC0`: фиксация состояния репозитория

Состояние: материализовано в ветке. Контракт слит в `main`
`8429f54257685a879b0a44499d5fa81eab7310ea` и повторно проверен; отдельная квитанция связывает
коммит слияния, контракт и его реестр. До слияния квитанции переход к `QW-LC1`
не разрешён.

```text
qwake_qw_lc0_repository_freeze_materialized=true
qwake_qw_lc0_repository_freeze_complete=false
qwake_qw_lc1_transition_permitted=false
qwake_qw_lc1_open=false
next_slice=QW-LC0-repository-freeze-merge
post_merge_next_slice=QW-LC1-transition
```

## Этап 26 — `QW-LC1`: переход к схеме требуемого результата

Состояние: переход материализован в ветке. После слияния и повторной проверки
может быть открыт самостоятельный срез определения канонической схемы
`R(a,s)`, обязательных наблюдаемых полей и оператора `~R`. Схема `Γ`,
отображение стоимости, реализация и выполнение в этот этап не входят.

```text
qwake_qw_lc1_transition_materialized=true
qwake_qw_lc1_transition_complete=false
qwake_qw_lc1_open=false
next_slice=QW-LC1-transition-merge
post_merge_next_slice=QW-LC1-required-response-schema
```
## Этап 26 — `QW-LC1`: схема требуемого результата зафиксирована

Состояние: контракт `stage3b-qwake-lc1-required-response-schema-v1` материализован в ветке. `R(a,s)` состоит
из именованных градиентов параметров, конечных beliefs и scalar loss.
Структурные поля сравниваются точно; численные записи проверяются отдельно
zero-safe оператором `~R` с профилями CPU/float64 и ROCm/float32. State/RNG и
fallback остаются задачей `QW-LC3`; `Γ`, `Φ`, `C` и `~C` — задачей `QW-LC2`.

```text
qwake_qw_lc1_transition_complete=true
qwake_qw_lc1_open=true
qwake_qw_lc1_required_response_schema_frozen=true
qwake_qw_lc1_contract_id=stage3b-qwake-lc1-required-response-schema-v1
qwake_qw_lc1_contract_sha256=sha256:c7923249c538b29a34f8ffcfcac987b9925a911eb107a085a166ab1d7ca22992
mandatory_observables_definition_frozen=true
response_equivalence_operator_definition_frozen=true
qwake_qw_lc1_complete=false
qwake_qw_lc2_transition_permitted=false
resource_trajectory_schema_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
next_slice=QW-LC1-repository-freeze
post_merge_next_slice=QW-LC1-repository-freeze
```
## Этап 27 — `QW-LC1`: фиксация состояния репозитория

Состояние: материализовано в ветке. Схема слита в `main` `59e3143ba105a5b298e2cd551b221b8f6dae96f7`
и повторно проверена; отдельная квитанция связывает коммит слияния, коммит
схемы, контракт и его реестр. До слияния квитанции `QW-LC1` не завершён и
переход к `QW-LC2` не разрешён.

```text
qwake_qw_lc1_repository_freeze_materialized=true
qwake_qw_lc1_repository_freeze_complete=false
qwake_qw_lc1_complete=false
qwake_qw_lc2_transition_permitted=false
resource_trajectory_schema_open=false
measurement_to_cost_mapping_open=false
cost_equivalence_operator_definition_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
next_slice=QW-LC1-repository-freeze-merge
post_merge_next_slice=QW-LC2-transition
```

## Этап 27 — `QW-LC2`: переход к модели ресурсов и стоимости

Состояние: переход материализован в ветке. После слияния и повторной проверки
может быть открыт самостоятельный контракт, фиксирующий `Γ(a,s)`, отображение
`Φ: Γ -> C` и `~C`. Поля, единицы, агрегация, Pareto-правило и запрет двойного
учёта будут определены только в этом будущем контракте. Реализация и выполнение
в переход не входят.

```text
qwake_qw_lc2_transition_materialized=true
qwake_qw_lc2_transition_complete=false
qwake_qw_lc2_open=false
next_slice=QW-LC2-transition-merge
post_merge_next_slice=QW-LC2-resource-cost-contract
```

## Этап 28 — `QW-LC2`: контракт ресурсов и стоимости

Состояние: контракт материализован в ветке. `Γ`, `Φ`, `C`, `~C`, профили,
допуски, Pareto-правило и tie-break зафиксированы. До завершения `QW-LC2`
требуется отдельная фиксация состояния репозитория. `QW-LC3`, реализация,
выполнение и научная кампания остаются закрытыми.

```text
qwake_qw_lc2_resource_cost_contract_frozen=true
qwake_qw_lc2_complete=false
qwake_qw_lc3_transition_permitted=false
next_slice=QW-LC2-repository-freeze
```

## Этап 29 — `QW-LC2`: фиксация состояния репозитория

Состояние: квитанция материализована в ветке. До её слияния `QW-LC2`
не завершён и переход к `QW-LC3` запрещён.

```text
qwake_qw_lc2_repository_freeze_materialized=true
qwake_qw_lc2_repository_freeze_complete=false
qwake_qw_lc2_complete=false
qwake_qw_lc3_transition_permitted=false
next_slice=QW-LC2-repository-freeze-merge
post_merge_next_slice=QW-LC3-transition
```

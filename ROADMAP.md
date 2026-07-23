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

## Этап 20 — `QW-2`: контракт особого случая `QWake-FP`

Заморозить `FixedPred`, `eta=1`, `stage2_baseline`, architecture, horizon,
snapshot boundaries, task-relative response, primary defect, `A0/A1/A2`,
analytic registry, cost schema, baselines, role matrix и receipt requirements.

## Этап 21 — `QW-3`: реализация superset pipeline

До первого научного freeze реализовать весь обязательный код:

```text
collector
A0/A1/A2
analytic registry
canonical suffix and post-action O
cost instrumentation
opportunity and recognizability analysis
policy interpreter
baseline and ablation replay
shadow confirmatory evaluation
replication evaluation
sealing and publication export
```

Manifest не загружает произвольный код и может активировать только встроенные
capabilities.

## Этап 22 — `QW-4`: pre-freeze validation

Выполнить static/unit/integration checks, CPU/ROCm smoke, permission matrix,
negative permission tests, observer-on/off non-interference, deterministic
replay, schema tests, corrupt/missing manifest tests, receipt-chain tests и
baseline replay tests.

Выключенная capability не должна вызываться, читать tensors, выделять память,
синхронизировать устройство или создавать output.

## Этап 23 — `QW-5`: единая заморозка scientific image

Зафиксировать source commit/tree, Torch2PC commit, image digest, code manifest и
версии output/capability/policy schemas. Между C1/C2/C3/R executable code и
зависимости не меняются.

Существенная ошибка после freeze требует нового digest и protocol version;
старые evidence сохраняются и не переписываются.

## Этап 24 — `QW-6`: `C1_COLLECTION` и opportunity

Тем же образом собрать полные temporal trajectories, `A0/A1/A2`, analytic
outputs, edge costs, canonical suffix и post-action oracle labels.

Opportunity gate:

```text
exists_preterminal_sufficient_state=true
potential_avoided_cost_exceeds_control_overhead_lower_bound=true
```

При отрицательном gate policy selection не обязательна; результат фиксируется
как bounded negative finding.

## Этап 25 — `QW-7`: `C2_CALIBRATION` и policy freeze

На calibration partition сравнить `A0`, `A0+A1`, `A0+A1+A2` и
`A0+A1+A2+analytics`, выполнить baselines и nested ablations, затем выбрать
простейшую безопасную почти недоминируемую policy.

`SELECT_POLICY` и `FREEZE_POLICY` разрешены только здесь. Confirmatory access
закрыт. Выход — frozen policy manifest и sealed C2 receipt.

## Этап 26 — `QW-8`: `C3_CONFIRMATORY`

На untouched model seeds загрузить frozen policy и выполнить shadow evaluation,
всегда завершая canonical suffix для post-action audit.

Порядок решений неизменен:

```text
safety
coverage
net cost
```

После открытия partition запрещены изменения features, thresholds, analytic
order, primary defect, baselines и cost mapping.

## Этап 27 — `QW-9`: replication без retuning

Тем же image digest и policy manifest выполнить одну заранее выбранную
репликацию, предпочтительно `MNIST` с той же архитектурой. Изменение policy или
thresholds запрещено. Failure переноса является допустимым результатом.

## Этап 28 — `QW-10`: synthesis, диссертация и publication gate

Объединить Stage 1/2, Stage 3A, B0, SI-MA0/1, B1/B2, EX-IF0, opportunity,
recognizability, confirmatory safety/coverage/cost, ablations и replication.

Publication открывается отдельным bounded решением только после sealed C1, C2,
C3 и replication receipt либо заранее зарегистрированного отказа от
replication.

Полный план: [ограниченная проверка QWake-FP](docs/qwake-fp-experimental-plan.md).

## Граница после магистерской работы — перспективная PhD-линия

После завершения текущего критического пути возможна отдельная программа
`QWake-SPC`: переход от
[спайкоподобной управляющей динамики](docs/glossary.md#term-spike-like-control-dynamics)
QWake-PC к нативным spikes, spike-native переносу ошибок, локальному обучению и
нейроморфной проверке. Эта программа не является этапом 21, не открывает
выполнение и не изменяет критерии завершения магистерской работы.

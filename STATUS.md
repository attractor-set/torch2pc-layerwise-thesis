# Статус исследования

[English version](STATUS_EN.md)

На 23 июля 2026 года опубликованы неизменяемые результаты Stage 1/2, Stage 3A,
Stage 3B B0, `SI-MA0` и `SI-MA1`. Подтверждающие B1 и B2 запечатаны с
положительными решениями. Новый пакет `v2`
[сопоставленного профилирования](docs/glossary.md#term-matched-profiling)
был prospectively связан с этими admissions, прошёл immutable-image,
ROCm/float32 preflight, authorization и dry-run gates, после чего завершены
288/288 ячеек в 96 matched blocks. Runtime validation прошла, failures и
повторы отсутствуют, а компактный evidence package запечатан и сохранён.
Post-collection/pre-analysis протокол описательного анализа уже
зафиксирован. Зарегистрированное ядро реализовано и проверено на полной
синтетической матрице. Pre-execution hardening подтвердил происхождение,
согласованность 288/1440/96 compact-таблиц и настоящий `Zstandard` кадр.
Машиночитаемый execution request, фактический runtime preflight и отдельная
authorization зафиксированы. Единственная read-only попытка выполнена на
проверенном `main`, точный 18-файловый выход независимо проверен и связан
внешним seal с receipt и audit package. Output опубликован bounded tagged action, а точный remote provenance сохранён
frozen publication receipt. Публикация разрешена только в пределах запечатанного
описательного анализа. `EX-IF0` теперь отдельно зафиксировал `stage2_baseline`
как канонический точный reference и правило минимального устойчиво достаточного
свипа; выполнение, создание oracle-меток, признаки и управление остаются
закрытыми.

Полный Stage 3B остаётся незавершённым.

## Машинно-проверяемая граница текущего состояния

```text
matched_profiling_manifest_cells=288
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

Эти строки описывают уже существующий контракт и не являются новым решением
о допуске.

## `QW-1`: чистый контракт QWake

Чистое ядро `QW-1` реализовано без зависимостей от Torch2PC, PyTorch, GPU,
файловой системы или subprocess. Оно фиксирует конечные типы состояния,
наблюдений, аналитики, действий, admission, стоимости, post-action oracle и
provenance; deny-all permission model; role-bound allowlists; sealed receipt
requirements; и детерминированный replay. Реализация не исполняет FixedPred и
не открывает ни одну научную кампанию.

```text
qwake_core_contract_implemented=true
qwake_core_contract_pure_python=true
qwake_core_contract_torch2pc_dependency=false
qwake_core_contract_gpu_dependency=false
qwake_permission_default=deny_all
qwake_capability_registry_closed=true
qwake_role_allowlists_fail_closed=true
qwake_receipt_chain_contract_implemented=true
qwake_deterministic_replay_contract_implemented=true
qwake_oracle_pre_action_access_permitted=false
qwake_scientific_execution_open=false
qwake_next_stage=QW-2
```

## `QW-2`: контракт особого случая `QWake-FP`

`QW-2` завершён как чистая и машиночитаемая заморозка единственного
обязательного частного случая. Python-spec, `ADR-043`, canonical JSON и
`SHA256SUMS` фиксируют `FixedPred`, `eta=1`, `stage2_baseline`, `lenet_classic`,
EX-IF0 endpoint defect, точные накопительные `A0/A1/A2`, конечный analytic
registry, B0-B7, P0-P2, cost mapping и наследуемые QW-1 role/receipt rules.
Ни одна вычислительная возможность не открыта. Эта фиксация только устраняет неоднозначность будущей реализации и сохраняет прежние запреты на выполнение, сбор данных и доступ к проверочной выборке.

```text
qwake_fp_special_case_contract_frozen=true
qwake_fp_special_case_contract_id=stage3b-qwake-fp-special-case-v1
qwake_fp_special_case_contract_sha256=968457365ddc1c94a814e0f7712d30d0154afd0c96d8464bff46a31e61ad3698
qwake_fp_method=fixedpred
qwake_fp_eta=1
qwake_fp_canonical_executor=stage2_baseline
qwake_fp_architecture=lenet_classic
qwake_fp_horizon_rule=registered_inference_steps
qwake_fp_observation_registry=A0,A1,A2
qwake_fp_analytic_registry=rosenbaum_wavefront_status_v1,residual_persistence_v1,cost_dominance_v1
qwake_fp_baseline_registry=B0,B1,B2,B3,B4,B5,B6,B7
qwake_fp_paired_validation=P0,P1,P2
qwake_fp_role_matrix_inherited_from_qw1=true
qwake_fp_scientific_execution_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
qwake_next_stage=QW-3
```

## Сводка состояния

| Компонент | Подтверждённое состояние |
|---|---|
| Пилот | 96/96; тестовая выборка не использовалась |
| Stage 1 / Stage 2 | 80/80 и 80/80 |
| Stage 3A | подтверждающая послойная диагностика и публикация завершены |
| Stage 3B B0 | 96/96 ячеек ROCm/float32; доказательные материалы и анализ опубликованы |
| `SI-MA0` | `REC/OBS/VER/CMP=true`, `COST=false`; общий отрицательный результат сохранён |
| `SI-MA1` | 10 `model_seed`, 180 сопоставленных блоков; `CAL-COST-MA1=true`, итог `pass` |
| Теоретическое условие B1/B2 | пакет `PC-TREF`/`PC-CATM` опубликован |
| Предварительная регистрация B1/B2 | завершена; тег `stage3b-b1-b2-prereg-v1` |
| B1 `isolated_layer_vjp` | confirmatory `EQ-B1=pass`; 120/120 пар |
| B2 `composite_vjp` | `EQ-B2-CONFIRMATORY=pass`; 120/120 троек, 240/240 сравнений, 0 failed pairs; derived `EQ-B2` сохранён |
| Запрос и манифест сопоставленного профилирования | новый `v2` refreeze сохранён; исторический `v1` неизменен |
| Исполнитель сопоставленного профилирования | реализация с учётом кандидата завершена |
| Выполнение сопоставленного профилирования | 288/288 ячеек, 96/96 блоков, 0 failures; sealed evidence сохранён |
| Описательный анализ сопоставленного профилирования | единственная попытка выполнена; 18 файлов проверены и опубликованы; audit, seal и publication receipt зафиксированы |
| `EX-IF0` | `stage2_baseline` зафиксирован как canonical exact reference; suffix-stable sweep rule frozen; execution и labels закрыты |
| Тестовая выборка | закрыта |
| Полный Stage 3B | `full_stage3b_campaign_complete=false` |

## Границы опубликованных результатов

### Stage 3A

В области FashionMNIST, `lenet_classic` и `model_seed=0..9`:

- `FixedPred` почти сохраняет направление градиента, но уменьшает его норму
  в ранних слоях;
- `Strict` в скрытых слоях отличается от BP по направлению и масштабу;
- представления `FixedPred` ближе к BP, чем представления `Strict`;
- отдельные слои, пакеты и изображения не считаются независимыми моделями.

Результаты ограничены зарегистрированными контрольными точками, реализацией
и вычислительной средой.

### Stage 3B B0

B0 закрепил `stage2_baseline` для `FixedPred` и `Strict` в синтетической
матрице ROCm/float32. В зарегистрированной области:

- медианное отношение Strict/FixedPred по времени устройства: `2.327×`;
- отношение пиковой выделенной памяти: `1.328×`;
- `state_inference` — основная область времени;
- отношение сохранённых тензоров в `state_inference`: `11.998×`.

Это описательный инженерный анализ, а не универсальное ранжирование методов.

### `SI-MA0` и `SI-MA1`

`SI-MA0` сохранил отрицательный итог после сбоя `COST-MA0`.
`SI-MA1` отдельно проверил калибровку наблюдателя и завершился с
`CAL-COST-MA1=true`, `SI-MA1=pass`. Итог `SI-MA1` не переписывает результат
`SI-MA0` и не включает стоимость будущего оценивателя `ECZ`, выбор действий,
проверку резервного перехода или сквозную выгоду B1/B2.

### Допуск B1/B2

Confirmatory B1 прошёл CPU `float64` и ROCm `float32` на 120/120 парах.
B2 прошёл инженерный smoke, а затем подтверждающую кампанию на 120/120
тройках и 240/240 прямых сравнениях. `EQ-B2-CONFIRMATORY=pass` запечатан;
derived `EQ-B2` связан с ним SHA-256. Эта цепочка допуска позволила выполнить
новое matched profiling `v2`. Само выполнение завершено, но сравнительные
выводы ещё не сформированы.

## Текущий переход

Запечатанный набор сопоставленного профилирования опубликован в
`results/stage-3/profiling/matched/stage3b-matched-profiling-e1dcfb2-v1/`.
Он содержит 288 агрегированных ячеек, 1440 строк повторов, 96 matched-block
сводок, 288 append-only histories, 96 untimed correctness records, поток
событий локальности, environment lock и runtime inventory. Test split не
использовался.

После однократного анализа, независимого audit, output sealing и успешного tagged publication action состояние зафиксировано так:

```text
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
full_stage3b_campaign_complete=false
```

Release `stage3b-matched-profiling-evidence-v1` опубликован bounded tagged
action, а receipt `stage3b-matched-descriptive-analysis-publication-receipt-v1`
связывает publication commit, успешный workflow run, release ID, время и digest
assets. Публикация не разрешает утверждения о превосходстве или test split.
`EX-IF0 v1` отдельно выбрал `stage2_baseline` как canonical exact reference,
зафиксировал decision epoch, task-relative endpoint, oracle margin и полную
suffix-stability для минимального достаточного свипа. Эта design freeze не
разрешает `A11-OFF0`, oracle-label generation, feature collection, predictor,
QWake-PC или выполнение рекурсивных агрегатов.

ADR-042 заменяет широкий post-publication critical path ограниченной проверкой
одной [QWake-FP](docs/glossary.md#term-qwake-fp). Общий QWake-PC остаётся
спецификацией, а обязательный эксперимент относится только к corrected
Rosenbaum FixedPred при `eta=1`. Следующий допустимый этап — docs-only `QW-0`,
после которого реализуется один permission-gated superset pipeline до единой
заморозки scientific image.

```text
qwake_general_specification_frozen=true
qwake_fp_only_mandatory_implementation=true
qwake_fp_validation_case=corrected_rosenbaum_fixedpred_eta1
execution_image_strategy=single_immutable_superset_image
same_image_digest_required_across_c1_c2_c3_r=true
stage_activation=fail_closed_permission_manifest
qwake_fp_execution_permitted=false
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
```

## Происхождение

| Артефакт | Идентификатор |
|---|---|
| B0 evidence | `stage3b-b0-evidence-v1` |
| B0 analysis | `stage3b-b0-analysis-evidence-v1` |
| `SI-MA1` preregistration | `stage3b-si-ma1-prereg-v1` |
| `SI-MA1` implementation | `stage3b-si-ma1-implementation-v1` |
| `SI-MA1` execution | `stage3b-si-ma1-confirmatory-execution-v1` |
| `SI-MA1` final | `stage3b-si-ma1-confirmatory-v1` |
| B1/B2 preregistration | `stage3b-b1-b2-prereg-v1` |
| Matched-profiling opening merge | `a249d35` |
| Candidate-aware runner implementation | `d611cb7` |
| Candidate-aware runner merge | `a44e7c8` |
| B2 confirmatory source | `63885e530fa38540ef684a6820a966eee96a58f9` |
| B2 confirmatory evidence | `stage3b-b2-confirmatory-63885e5-v1` |
| Matched-profiling execution source | `e1dcfb26823e1191b98d2aa2a598499b13197583` |
| Matched-profiling immutable image | `sha256:3c269b4278026b5b69968b3265b506ce626f2baf693859989de3371d639da4d0` |
| Matched-profiling evidence | `stage3b-matched-profiling-e1dcfb2-v1` |
| Published bounded release | `stage3b-matched-profiling-evidence-v1` |
| Publication action | `stage3b-matched-descriptive-analysis-publication-v1` |
| Publication receipt | `stage3b-matched-descriptive-analysis-publication-receipt-v1` |

Документационные изменения не пересоздают опубликованные результаты.

## FixedPred sufficiency и D/U/S

ADR-039 фиксирует следующий частный случай без разрешения выполнения:

```text
fixedpred_sufficiency_dus_design_frozen=true
fixedpred_sufficiency_method=fixedpred
fixedpred_sufficiency_exact_graph=stage2_baseline
rosenbaum_wavefront_role=analytic_positive_control
joint_vjp_role=exact_graph_organization_control
dus_controls_execution=false
oracle_label_generation_open=false
feature_collection_permitted=false
a11_off0_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

Следующий допустимый slice ограничен рефакторингом и synthetic validation.
Frozen evidence, `EX-IF0`, historical identifiers и опубликованные решения не
изменяются.

## Интегрированная модель фронтира

ADR-041 сохраняет ADR-039 и ADR-040 как исторические решения и задаёт текущую
семантику переходов, допуска, стоимости и обязательного scope. `O` отделён от
развёртываемой оси `A0 -> A1 -> A2`; аналитика является самостоятельным
измеряемым переходом, а `DONE` означает уже допущенный теневой исход.
Обязательный путь ограничен temporal `FixedPred`; рекурсивные масштабы и active
control остаются условными. Научный сбор и закрытые данные не открываются.

Корректирующая фиксация устраняет неоднозначности документации, но не объявляет положительный научный результат и не меняет запечатанные доказательные материалы. Любой последующий эксперимент требует отдельного решения о допуске.

```text
integrated_frontier_corrective_semantics_frozen=true
frontier_action_alphabet=ACCEPT_FRONTIER,ADVANCE_FRONTIER,COMPLETE_SUFFIX
frontier_advance_kinds=OBSERVATION,ANALYTIC,COMPUTE
deployable_observation_level_order=A0,A1,A2
oracle_level=O
oracle_availability=post_action_only
oracle_is_frontier_action=false
within_snapshot_observation_monotone=true
compute_transition_resets_current_observation=A0
analytic_registry_finite_and_frozen=true
measurement_to_decision_cost_mapping_required=true
done_semantics=admitted_shadow_outcome
mandatory_thesis_scope=temporal_fixedpred_prefix
recursive_multiscale_scope=conditional_extension
integrated_frontier_controls_execution=false
oracle_label_generation_open=false
feature_collection_permitted=false
a11_off0_execution_open=false
recursive_aggregate_execution_open=false
policy_activation_permitted=false
test_dataset_access=false
full_stage3b_campaign_complete=false
```

## Ограниченная проверка `QWake-FP`

[ADR-042](docs/decisions/ADR-042-stage3b-qwake-fp-bounded-validation-and-single-image-gating.md)
фиксирует общий QWake-PC как спецификацию и QWake-FP как единственную
обязательную реализацию. Кампании `C1_COLLECTION`, `C2_CALIBRATION`,
`C3_CONFIRMATORY` и `R_REPLICATION` должны использовать один image digest и
различаться только хешированными request/policy manifests и разрешениями.

Permission проверяется внутри effectful функций. Выключенная capability не
исполняется. `C2` является строго offline стадией над sealed C1 artifacts:
FixedPred, новый сбор A0/A1/A2, live analytics, новый suffix/oracle и confirmatory
access в ней запрещены. Policy selection разрешён только в `C2`. C3 использует
untouched model seeds, а R — ту же policy без retuning. Safety проверяется раньше
coverage, coverage — раньше cost.


Практический смысл этой фиксации состоит в том, что все программные ветви,
необходимые для будущих доказательных стадий, должны быть подготовлены и
проверены до единственной заморозки образа. После неё меняются только
разрешения, наборы начальных значений, раздел данных и хешированные запросы.
Такое разделение исключает скрытую замену реализации между калибровкой и
подтверждающей проверкой и одновременно сохраняет независимость данных.

Отключённая возможность считается действительно отсутствующей в исполняемом
пути: она не должна читать тензоры, выделять память, создавать синхронизацию или
записывать результат. Поэтому сравнимость стадий опирается не только на один
образ, но и на проверяемое отсутствие побочных действий закрытых возможностей.

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
permission_checks_at_effect_boundaries=true
disabled_capability_executes=false
policy_representation=frozen_data_manifest
policy_selection_with_confirmatory_access_forbidden=true
sealed_receipt_chain_required=true
untouched_confirmatory_seeds_required=true
replication_without_retuning_required=true
publication_baselines_required=true
nested_ablation_required=true
trajectory_benchmark_planned=true
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

## Реализация superset pipeline `QW-3`

`QW-3` реализует backend-neutral обязательный контур поверх `QW-1/QW-2`:
закрытый реестр встроенных компонентов, effect-local planning, неизменяемую
trajectory schema, точные накопительные `A0/A1/A2`, конечный policy interpreter,
B0–B7 и nested ablations, недублирующее cost mapping, opportunity и
recognizability, shadow/replication evaluation, чистое sealing и формирование
`rendered_not_published` publication bundle.

Модуль не импортирует Torch/Torch2PC, не выполняет FixedPred, не читает GPU и не
пишет артефакты. Live adapters ещё не связаны; все кампании и scientific image
freeze остаются закрытыми. Следующий этап — `QW-4` pre-freeze validation и
привязка канонических CPU/ROCm adapter/smoke contracts.

Реализация на этом шаге ограничена проверяемой логикой координации и обработки неизменяемых записей. Она не считается доказательством корректности наблюдателя на реальном устройстве и не заменяет последующие парные проверки, проверку невмешательства, измерение накладных расходов и канонический прогон в контейнере.

```text
qwake_fp_superset_pipeline_implemented=true
qwake_fp_superset_pipeline_execution_open=false
qwake_fp_live_adapters_bound=false
qwake_fp_component_registry_closed=true
qwake_fp_offline_replay_implemented=true
qwake_fp_publication_export_mode=rendered_not_published
qwake_fp_next_stage=QW-4
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
```

## `QW-4A`: контур предварительной проверки и фиксация запроса

`QW-4A` добавляет чистый контур предварительной проверки и замораживает запрос
`stage3b-qwake-fp-pre-freeze-validation-v1`. Запрос связывает контракт `QW-2`,
две вычислительные линии `CPU/ROCm`, точные равенства для `P0/P1/P2`, измерения
наблюдателя, отрицательные проверки эффектов, вложенность `A0/A1`, изоляцию
оракула после действия, отображение стоимости, целостность манифеста и цепочку
квитанций. Запрос не является разрешением на выполнение и не является
доказательным материалом.

Канонический загрузчик `FixedPred` зарегистрирован как существующий, но не имеет
разрешения на запуск. Новые адаптеры наблюдения, оракула и измерения стоимости
остаются несвязанными. Проверочные запуски, запечатанный инженерный отчёт и
заморозка научного образа ещё не выполнены. Следующим шагом остаётся `QW-4B`, а
не `QW-5`.

Это разделение сохраняет закрытую при ошибке границу: наличие проверяющего кода
не означает разрешения использовать модель, читать тензоры или создавать
оракульные метки. Переход к заморозке образа допускается только после успешных
сопоставленных проверок на обеих вычислительных линиях и независимой проверки
полученного отчёта.

```text
qwake_fp_pre_freeze_validation_request_frozen=true
qwake_fp_pre_freeze_validation_request_id=stage3b-qwake-fp-pre-freeze-validation-v1
qwake_fp_pre_freeze_validation_harness_implemented=true
qwake_fp_pre_freeze_validation_complete=false
qwake_fp_runtime_authorization_issued=false
qwake_fp_pre_freeze_evidence_generated=false
qwake_fp_live_adapters_bound=false
qwake_fp_scientific_image_freeze_permitted=false
qwake_next_stage=QW-4-runtime-validation
qwake_fp_next_stage=QW-4-runtime-validation
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
```

## `QW-4B-I`: runtime-validation implementation

Реализованы deny-all runtime preflight, строгая проверка source/image/Torch2PC
identity, валидатор будущего single-run authorization, effect-local adapter
symbols, concrete Torch/Torch2PC backend для `stage2_baseline`, all-snapshot
observer, последовательный matched runner с восстановлением state/RNG,
цепочка static-validation receipt и authorization-only execution CLI. Этот
slice не выпускает authorization, не выполняет FixedPred самопроизвольно и не
создаёт evidence. Следующим остаётся `QW-4B-F` runtime
freeze, а не `QW-5`.

```text
qwake_fp_runtime_validation_implementation_complete=true
qwake_fp_runtime_preflight_implemented=true
qwake_fp_runtime_authorization_validator_implemented=true
qwake_fp_runtime_adapter_symbols_bound=true
qwake_fp_matched_runtime_runner_implemented=true
qwake_fp_runtime_report_sealer_implemented=true
qwake_fp_canonical_torch_backend_implemented=true
qwake_fp_all_snapshot_observer_implemented=true
qwake_fp_authorized_execution_cli_implemented=true
qwake_fp_static_validation_receipt_chain_implemented=true
qwake_fp_runtime_authorization_issued=false
qwake_fp_runtime_validation_performed=false
qwake_fp_pre_freeze_evidence_generated=false
qwake_fp_pre_freeze_validation_complete=false
qwake_fp_live_adapters_bound=false
qwake_fp_scientific_image_freeze_permitted=false
qwake_next_stage=QW-4-runtime-validation
qwake_fp_next_stage=QW-4-runtime-validation
qwake_fp_next_slice=QW-4-runtime-freeze
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
oracle_label_generation_open=false
feature_collection_permitted=false
policy_activation_permitted=false
test_dataset_access=false
```

## `QW-4B-DOC-R1`: полный рефакторинг активного плана

Старый кандидат `QW-4B-F-v1` выведен из обращения до выполнения. Его байты,
журналы и разрешение сохранены во внешнем каталоге аудита, но повторное
использование запрещено. Научные и инженерные результаты не создавались.

Активный план теперь разделяет `R`, `M`, `Γ` и `C`, вводит семейство
`LOCAL_COMPUTE`, ограничивает первый аналитический кандидат и устанавливает
единственную последовательность `QW-4B-F-v2 → QW-4B-E-v2 → QW-LC0…QW-LC4-E
→ QW-5 → C1 → C2 → C3 → R`.

После слияния этой ветки требуется новый неизменяемый образ. Только затем можно
заново получить предварительную проверку, квитанцию и одноразовое разрешение.

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
qwake_next_slice=QW-4B-new-image
qwake_post_baseline_next_slice=QW-LC0
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

## `QW-4B-F-v2`: новый образ и одноразовый допуск заморожены

После слияния `QW-4B-DOC-R1` собран новый неизменяемый образ из merge commit `e413bb1e13cee42f702512e499f994e90df21e45`. В нём повторно прошли статические, модульные и документальные проверки, затем была получена новая предварительная проверка CPU/ROCm и выпущено разрешение на одну инженерную попытку.

Разрешение повторно проверено официальной программой проверки и перенесено в `experiments/frozen/stage3b-qwake-fp-runtime-validation-freeze-v2` без изменения исходных байтов. Исполняющая команда не вызывалась, каталог результата не создавался, инженерные [доказательные материалы](docs/glossary.md#term-evidence) отсутствуют.

Текущее состояние означает только готовность строго ограниченного допуска. Оно не подтверждает невмешательство наблюдателей, корректность измерительной стоимости или пригодность механизма для будущей политики. Эти свойства должны быть получены и независимо проверены в следующем отдельном срезе.

Научная последовательность остаётся закрытой: данные тестовой выборки недоступны, создание научных меток запрещено, публикация не разрешена, а расширение локальных вычислений не может быть реализовано или выполнено до запечатанного базового отчёта.

```text
qwake_documentation_refactor_complete=true
qwake_old_runtime_authorization_retired=true
qwake_old_runtime_authorization_reuse_permitted=false
qwake_new_image_required=false
qwake_new_image_built=true
qwake_new_image_source_commit=e413bb1e13cee42f702512e499f994e90df21e45
qwake_new_image_digest=sha256:bd91fab26df5f91a3aba90b8cad38badccab3a1a7bfb20efe4126a88a13236c4
qwake_new_runtime_preflight_captured=true
qwake_new_runtime_authorization_issued=true
qwake_runtime_authorization_verified=true
qwake_runtime_validation_permitted=true
qwake_runtime_execution_performed=false
qwake_runtime_validation_performed=false
qwake_engineering_evidence_present=false
qwake_fp_execution_permitted=false
qwake_frozen_preflight_sha256=sha256:79ead4a0e757272c788acd90700d61c0e5a0509fe64168f83f47dc0963ce4d00
qwake_frozen_authorization_sha256=sha256:d22063efa0c458c2498577139fa322b952081d8356cd1a6511f25188b12206b6
qwake_frozen_receipt_chain_sha256=sha256:9eda60c6806581fea28021546b881d939e062c017b702a175105c56a25dea05d
qwake_frozen_authorized_cell_count=6
qwake_frozen_execution_count=1
qwake_authorized_output_root_absent=true
qwake_scientific_image_freeze_permitted=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
qwake_next_slice=QW-4B-E-v2
qwake_post_baseline_next_slice=QW-LC0
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

## `QW-4B-E-v2`: базовый инженерный отчёт выполнен и независимо восстановлен

Единственная разрешённая попытка выполнена из изолированного исходного commit
`e413bb1e13cee42f702512e499f994e90df21e45`. Исполнитель успешно завершил
шесть ячеек `CPU/ROCm × P0/P1/P2`, а неизменяемый output связан с отчётом
`sha256:54dba01d47814dc00fa53bd69c00865bd1c47754c017c7482c895162d3a86b82`.

Ошибка post-execution wrapper и два последующих дефекта recovery-аудита
сохранены как provenance. Независимый recovery-v3 подтвердил равенство
authorization по JSON и загруженной модели, успешность обеих линий,
невмешательство наблюдений, oracle isolation и нулевые эффекты отключённых
возможностей. Runtime повторно не выполнялся.

Текущий срез материализует точный output, полный пакет аудита и внешнюю печать.
До слияния repository seal и отдельного открытия семантики `QW-LC0` локальное
расширение остаётся закрытым. Отчёт является только инженерным: научные данные,
публикация и test split не открыты.

```text
qwake_qw4b_e_v2_materialized=true
qwake_qw4b_e_v2_repository_evidence_sealed=false
qwake_qw4b_e_v2_runner_status=0
qwake_qw4b_e_v2_authorization_consumed=true
qwake_qw4b_e_v2_retry_permitted=false
qwake_qw4b_e_v2_runtime_rerun_performed=false
qwake_qw4b_e_v2_runtime_execution_performed=true
qwake_qw4b_e_v2_runtime_execution_completed=true
qwake_qw4b_e_v2_authorized_cell_count=6
qwake_qw4b_e_v2_cpu_lane_passed=true
qwake_qw4b_e_v2_rocm_lane_passed=true
qwake_qw4b_e_v2_engineering_evidence_present=true
qwake_qw4b_e_v2_image_freeze_eligible=true
qwake_qw4b_e_v2_report_sha256=sha256:54dba01d47814dc00fa53bd69c00865bd1c47754c017c7482c895162d3a86b82
qwake_qw4b_e_v2_scientific_evidence=false
qwake_qw4b_e_v2_scientific_execution_open=false
qwake_qw4b_e_v2_test_dataset_access=false
qwake_qw4b_e_v2_publication_permitted=false
qwake_qw_lc0_open=false
qwake_next_slice=QW-4B-E-v2-repository-seal
qwake_post_merge_next_slice=QW-LC0
```


## `QW-LC0`: post-merge переход открыт

Repository seal `QW-4B-E-v2` слит в `main` commit
`4f23b752a40ae05de9fc7ee49c9962c44083b71d`. Три evidence-слоя повторно проверены; их байты и
digest-идентичности не изменены.

Открывается только документационная фиксация семантики и области `QW-LC0`.
Реализация и выполнение `LOCAL_COMPUTE`, научный образ, C1/C2/C3/R, test split
и публикация остаются закрытыми.

```text
qwake_qw4b_e_v2_repository_evidence_sealed=true
qwake_qw4b_e_v2_repository_seal_commit=26bc0ef635e13dba719d3356fe17382f0037d1df
qwake_qw4b_e_v2_repository_merge_commit=4f23b752a40ae05de9fc7ee49c9962c44083b71d
qwake_qw4b_e_v2_post_merge_verification_passed=true
qwake_qw_lc0_transition_permitted=true
qwake_qw_lc0_open=true
qwake_qw_lc0_semantics_scope_frozen=false
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
qwake_next_slice=QW-LC0
qwake_post_lc0_next_slice=QW-LC1
```


## `QW-LC0`: семантика и область зафиксированы

Контракт `stage3b-qwake-lc0-semantics-scope-v1` нормативно разделяет `R/M/Γ/C`, фиксирует два вида
`LOCAL_COMPUTE` и ограничивает первый кандидат особым случаем `FixedPred`,
`eta=1`, `lenet_classic`, `stage2_baseline`. Он не содержит реализации или
эмпирического подтверждения кандидата.

```text
qwake_qw_lc0_semantics_scope_frozen=true
qwake_qw_lc0_contract_id=stage3b-qwake-lc0-semantics-scope-v1
qwake_qw_lc0_contract_sha256=sha256:e68e953aa3d5c425678d54b8dd3b756e706e5cc1a1c4862d4c0ba0bda19bf3c3
qwake_qw_lc1_transition_permitted=false
qwake_qw_lc1_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC0-repository-freeze
qwake_post_merge_next_slice=QW-LC1
```

## `QW-LC0`: фиксация состояния репозитория материализована

Контракт `stage3b-qwake-lc0-semantics-scope-v1` слит в `main` коммитом
`8429f54257685a879b0a44499d5fa81eab7310ea` и повторно проверен без изменения 22-файлового дерева.
Материализована отдельная квитанция состояния репозитория. До её слияния
переход к `QW-LC1` запрещён, а реализация и выполнение остаются закрытыми.
Квитанция предназначена только для воспроизводимой проверки включения контракта в основную ветку. Она не подтверждает корректность аналитического завершения, не сравнивает стоимость механизмов и не разрешает вычислительные действия.

```text
qwake_qw_lc0_semantics_scope_frozen=true
qwake_qw_lc0_contract_id=stage3b-qwake-lc0-semantics-scope-v1
qwake_qw_lc0_contract_sha256=sha256:e68e953aa3d5c425678d54b8dd3b756e706e5cc1a1c4862d4c0ba0bda19bf3c3
qwake_qw_lc0_repository_main_commit=8429f54257685a879b0a44499d5fa81eab7310ea
qwake_qw_lc0_repository_freeze_materialized=true
qwake_qw_lc0_repository_freeze_complete=false
qwake_qw_lc1_transition_permitted=false
qwake_qw_lc1_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC0-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC1-transition
```

## `QW-LC1`: переход материализован

Фиксация состояния репозитория `QW-LC0` завершена после слияния и повторной
проверки `main` `0fbd54be337665e06ad63b6d9c7f8ca978ab75ee`. Материализована отдельная
квитанция перехода. Она ограничивает будущий `QW-LC1` определением схемы
требуемого результата `R(a,s)`, обязательных наблюдаемых полей и оператора
`~R`, но не определяет их содержимое. До слияния перехода сам `QW-LC1`,
траектория `Γ`, стоимость, реализация и выполнение остаются закрытыми.

```text
qwake_qw_lc0_repository_freeze_complete=true
qwake_qw_lc1_transition_permitted=true
qwake_qw_lc1_transition_materialized=true
qwake_qw_lc1_transition_complete=false
qwake_qw_lc1_transition_id=stage3b-qwake-lc1-transition-v1
qwake_qw_lc1_transition_sha256=sha256:9cafcad4d6ee3245c48ca2ff531dc5985ea4e670cb465fdcfaf2b99d376d5db4
qwake_qw_lc1_open=false
qwake_qw_lc1_required_response_schema_open=false
mandatory_observables_definition_open=false
response_equivalence_operator_definition_open=false
resource_trajectory_schema_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC1-transition-merge
qwake_post_merge_next_slice=QW-LC1-required-response-schema
```
## `QW-LC1`: схема требуемого результата зафиксирована

Переход `QW-LC1` слит в `main` `c3533fcb63ffc869faddbaa99645c9099d16d1cc` и повторно проверен. Контракт
`stage3b-qwake-lc1-required-response-schema-v1` фиксирует канонический `R(a,s)`, обязательные наблюдаемые поля
ответа и правило `~R`, безопасное для нулевых норм. Точное равенство контрольных
сумм является достаточным, но не обязательным условием. Отношение с численным
допуском не считается транзитивным. Схема не содержит реализации и не
подтверждает аналитический кандидат.

Каждый ответ включает именованные градиенты параметров, конечные представления
слоёв и скалярную функцию потерь. До численной проверки должны точно совпасть
схема, ссылка на состояние, профиль сравнения, порядок компонентов, имена,
позиции, формы, типы данных и число элементов. Это не позволяет скрыть
структурное расхождение малой глобальной нормой.

Проверка чисел выполняется отдельно для каждой зарегистрированной записи.
Две записи с нормами ниже порога проходят условие направления, но всё равно
обязаны пройти ограничения относительной и максимальной абсолютной ошибки.
Если активна только одна запись, сравнение завершается отказом.

```text
qwake_qw_lc1_transition_complete=true
qwake_qw_lc1_required_response_schema_permitted=true
qwake_qw_lc1_open=true
qwake_qw_lc1_required_response_schema_frozen=true
qwake_qw_lc1_contract_id=stage3b-qwake-lc1-required-response-schema-v1
qwake_qw_lc1_contract_sha256=sha256:c7923249c538b29a34f8ffcfcac987b9925a911eb107a085a166ab1d7ca22992
qwake_qw_lc1_contract_registry_sha256=sha256:4a5dca3848bd8ffb0f70013fb5c42a6f6427dd0e1752eb950f5332207b8e269f
mandatory_observables_definition_frozen=true
response_equivalence_operator_definition_frozen=true
qwake_qw_lc1_complete=false
qwake_qw_lc2_transition_permitted=false
resource_trajectory_schema_open=false
measurement_to_cost_mapping_open=false
cost_equivalence_operator_definition_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC1-repository-freeze
qwake_post_merge_next_slice=QW-LC1-repository-freeze
```
## `QW-LC1`: фиксация состояния репозитория материализована

Схема требуемого результата слита в `main` `59e3143ba105a5b298e2cd551b221b8f6dae96f7` и повторно
проверена. Коммит схемы `de2b5a37583b22946073390caa244bee35dd793b` сохранён вторым
родителем, точный 22-файловый состав и дерево схемы не изменились, а контракт и
реестр имеют ожидаемые контрольные суммы.

Двухфайловая квитанция `stage3b-qwake-lc1-repository-freeze-v1` связывает это состояние
`main` с контрактом `stage3b-qwake-lc1-required-response-schema-v1`. До слияния и отдельной
проверки квитанции `QW-LC1` остаётся незавершённым, переход к `QW-LC2`
запрещён, а ресурсная траектория, стоимость, реализация и выполнение закрыты.

```text
qwake_qw_lc1_required_response_schema_merged=true
qwake_qw_lc1_schema_main_commit=59e3143ba105a5b298e2cd551b221b8f6dae96f7
qwake_qw_lc1_schema_commit=de2b5a37583b22946073390caa244bee35dd793b
qwake_qw_lc1_repository_freeze_materialized=true
qwake_qw_lc1_repository_freeze_complete=false
qwake_qw_lc1_complete=false
qwake_qw_lc2_transition_permitted=false
resource_trajectory_schema_open=false
measurement_to_cost_mapping_open=false
cost_equivalence_operator_definition_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC1-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC2-transition
```

## `QW-LC2`: переход материализован

Фиксация состояния репозитория `QW-LC1` завершена после слияния и независимой
проверки `main` `9d073bc3c90eeda53ca03d0f7762b65da8749269`. Материализована отдельная квитанция перехода.
Она ограничивает будущий `QW-LC2` измерительной схемой `Γ(a,s)`, отображением
`Φ: Γ -> C` и оператором `~C`, но не определяет их поля, единицы, допуски или
значения. До слияния перехода сам `QW-LC2`, реализация и выполнение закрыты.

```text
qwake_qw_lc1_repository_freeze_complete=true
qwake_qw_lc1_complete=true
qwake_qw_lc2_transition_permitted=true
qwake_qw_lc2_transition_materialized=true
qwake_qw_lc2_transition_complete=false
qwake_qw_lc2_transition_id=stage3b-qwake-lc2-transition-v1
qwake_qw_lc2_transition_sha256=sha256:9a7e21fa573aa497e5c85ab92aade9e84e15dc0bd05e18e948ad8fac0194df23
qwake_qw_lc2_open=false
resource_trajectory_schema_open=false
measurement_to_cost_mapping_open=false
cost_equivalence_operator_definition_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
qwake_next_slice=QW-LC2-transition-merge
qwake_post_merge_next_slice=QW-LC2-resource-cost-contract
```

## `QW-LC2`: контракт ресурсов и стоимости материализован

После слияния и независимой проверки перехода на `main` `858403cbb2423ad3427ab7a042266880ca34c0b7`
материализован контракт `stage3b-qwake-lc2-resource-cost-contract-v1`. Он фиксирует каноническую исходную
траекторию `Γ(a,s;r,p)`, отображение `Φ` без двойного учёта, 11-полевой `C`,
инженерный теневой и будущий сквозной профили, покомпонентный `~C`,
Pareto-правило и детерминированное разрешение неоднозначности.

Сырые интервалы, пики памяти и артефакты остаются отделены от решенческого
вектора. Сквозная задержка не складывается с декомпозированными временами,
память не суммируется, а отрицательный остаток калибровки наблюдателя не
трактуется как отрицательная физическая стоимость. Проверка состояния,
восстановление ГПСЧ, проверка резервного суффикса, агрегация повторов,
реализация и выполнение остаются последующими срезами.

```text
qwake_qw_lc2_transition_complete=true
qwake_qw_lc2_open=true
qwake_qw_lc2_resource_cost_contract_frozen=true
qwake_qw_lc2_contract_id=stage3b-qwake-lc2-resource-cost-contract-v1
qwake_qw_lc2_contract_sha256=sha256:313dc969ab59db20ee27976d3158fca23ce511801e0dc7700dde0d2d002ab69d
qwake_qw_lc2_contract_registry_sha256=sha256:61763ad19c968dbad3eef16e5bee3a11d9dbfad74a7bf45dfc2e64cc022cf311
resource_trajectory_schema_open=false
resource_trajectory_schema_frozen=true
measurement_to_cost_mapping_open=false
measurement_to_cost_mapping_frozen=true
cost_equivalence_operator_definition_open=false
cost_equivalence_operator_definition_frozen=true
pareto_and_tie_break_rule_frozen=true
qwake_qw_lc2_complete=false
qwake_qw_lc3_transition_permitted=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
qwake_next_slice=QW-LC2-repository-freeze
```

## `QW-LC2`: фиксация состояния репозитория материализована

Контракт `stage3b-qwake-lc2-resource-cost-contract-v1` слит в `main` `8f24229bcf19736086fe6f0340bda26dd533936a` и независимо проверен.
Квитанция `stage3b-qwake-lc2-repository-freeze-v1` связывает это состояние
с коммитом контракта `3f1682765089b0819dcaaf9bb449c4c1bd155142` и его контрольными суммами.

До слияния квитанции `QW-LC2` незавершён, а `QW-LC3`, реализация и
выполнение закрыты.

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

## `QW-LC3`: переход материализован

Фиксация состояния репозитория `QW-LC2` завершена после слияния и независимой
проверки `main` `4f7c533047214398e7ec4dde9d58b5fc06964b90`. Коммит фиксации
`3f4310a05de5b7cd3db0cdb5c8f7cf4bbcb09150` сохранён в графе, дерево не
изменено, а квитанция и контракт ресурсов имеют ожидаемые контрольные суммы.

Материализована отдельная квитанция перехода
`stage3b-qwake-lc3-transition-v1`. Она ограничивает будущий `QW-LC3`
сопоставленной теневой проверкой, непрозрачной идентичностью общего состояния,
восстановлением ГПСЧ, полным точным резервным суффиксом и сопоставленной
агрегацией повторов. До слияния перехода сам `QW-LC3`, его определения,
реализация и выполнение закрыты.

```text
qwake_qw_lc2_repository_freeze_complete=true
qwake_qw_lc2_complete=true
qwake_qw_lc3_transition_permitted=true
qwake_qw_lc3_transition_materialized=true
qwake_qw_lc3_transition_complete=false
qwake_qw_lc3_transition_id=stage3b-qwake-lc3-transition-v1
qwake_qw_lc3_transition_sha256=sha256:c541703f8bc1d449aed88f175b83b9fc03e2574acb5c2be715b157be68733602
qwake_qw_lc3_open=false
matched_shadow_validation_protocol_open=false
opaque_state_ref_definition_open=false
rng_restoration_protocol_open=false
exact_reserve_suffix_validation_open=false
repeat_aggregation_protocol_open=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
qwake_scientific_image_freeze_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
qwake_next_slice=QW-LC3-transition-merge
qwake_post_merge_next_slice=QW-LC3-matched-shadow-validation-contract
```

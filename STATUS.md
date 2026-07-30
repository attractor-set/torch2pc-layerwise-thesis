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

## `QW-LC3`: контракт сопоставленной теневой проверки материализован

После слияния и независимой проверки перехода через PR №120 на `main`
`a7e0c4ec1978042d68abc7437e3005e4295e75ff` материализован контракт
`stage3b-qwake-lc3-matched-shadow-validation-contract-v1`. Он фиксирует
каноническую непрозрачную ссылку общего состояния, полный реестр и
восстановление ГПСЧ, двенадцать сбалансированных сопоставленных повторов, два
принудительных зонда полного точного резервного суффикса, покомпонентную
агрегацию стоимости и отдельную проверку эффекта порядка.

Каждая рука и резервный зонд начинаются из нового одноразового ответвления
одного неизменяемого снимка. `~R` должен пройти для всех двенадцати пар;
исключение повторов, голосование большинства и скаляризация стоимости
запрещены. Контракт не содержит реализации и не сообщает эмпирический результат.

```text
qwake_qw_lc3_transition_complete=true
qwake_qw_lc3_open=true
qwake_qw_lc3_matched_shadow_validation_contract_frozen=true
qwake_qw_lc3_contract_id=stage3b-qwake-lc3-matched-shadow-validation-contract-v1
qwake_qw_lc3_contract_sha256=sha256:e1512f29b3e3e3882001172df360e895e6e628b8ea8e4103b9574990775dd5d8
qwake_qw_lc3_contract_registry_sha256=sha256:2b001f3002add8d55ce75b02b1caba6bd3c655d177aeb02fe09026e2054dcef1
matched_shadow_validation_protocol_frozen=true
opaque_state_ref_definition_frozen=true
rng_restoration_protocol_frozen=true
exact_reserve_suffix_validation_frozen=true
repeat_aggregation_protocol_frozen=true
qwake_qw_lc3_complete=false
qwake_qw_lc4_implementation_permitted=false
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
qwake_next_slice=QW-LC3-repository-freeze
```

## `QW-LC3`: фиксация состояния репозитория материализована

Контракт `stage3b-qwake-lc3-matched-shadow-validation-contract-v1` слит через PR №121 в
`main` `71e73f56408c720334b8fa03e7133762c8bbcc43` и независимо проверен. Квитанция
`stage3b-qwake-lc3-repository-freeze-v1` связывает это состояние с коммитом
контракта `fb3f1cd4a4d3b4261db1179badcc1ccacddfe936` и его контрольными суммами.

До слияния квитанции `QW-LC3` незавершён, а `QW-LC4-I`, реализация и
выполнение закрыты.
Фиксация подтверждает только целостность уже принятого описания проверки. Она не подтверждает корректность будущего алгоритма, равенство результатов, снижение стоимости или готовность к научному запуску.
Проверяемое состояние остаётся подготовительным: оно сохраняет происхождение решений, исключает скрытое расширение области и требует отдельного допуска для каждого последующего шага. Любое вычисление до такого допуска считается запрещённым и не может использоваться как результат исследования.

```text
qwake_qw_lc3_matched_shadow_validation_contract_merged=true
qwake_qw_lc3_matched_shadow_validation_contract_complete=true
qwake_qw_lc3_contract_id=stage3b-qwake-lc3-matched-shadow-validation-contract-v1
qwake_qw_lc3_contract_sha256=sha256:e1512f29b3e3e3882001172df360e895e6e628b8ea8e4103b9574990775dd5d8
qwake_qw_lc3_repository_main_commit=71e73f56408c720334b8fa03e7133762c8bbcc43
qwake_qw_lc3_contract_commit=fb3f1cd4a4d3b4261db1179badcc1ccacddfe936
qwake_qw_lc3_repository_freeze_materialized=true
qwake_qw_lc3_repository_freeze_complete=false
qwake_qw_lc3_complete=false
qwake_qw_lc4_implementation_permitted=false
matched_shadow_validation_protocol_frozen=true
opaque_state_ref_definition_frozen=true
rng_restoration_protocol_frozen=true
exact_reserve_suffix_validation_frozen=true
repeat_aggregation_protocol_frozen=true
qwake_local_compute_implementation_open=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
qwake_next_slice=QW-LC3-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC4-I
```

## `QW-LC4-I`: ограниченная реализация материализована

Фиксация состояния репозитория `QW-LC3` слита через PR №122 в `main`
`7c6cbb6ba4941cf78b2bfec3e6e8955c2830a58b` и независимо проверена.
`QW-LC3` завершён. Пакет
`stage3b-qwake-lc4-i-bounded-implementation-v1` связывает ограниченный
аналитический кандидат FixedPred при `eta=1`, полный точный суффикс,
канонический контроль состояния и ГПСЧ, оператор ответа `QW-LC1`, отображение
стоимости `QW-LC2` и сбалансированную агрегацию двенадцати повторов.

Единственное разрешение на вызов в этом срезе предназначено только для
синтетических модульных тестов. Модуль не содержит интерфейса командной строки,
загрузчика набора данных, записи результатов, чтения разрешения рабочей среды
или научного исполнителя. Синтетические тесты не являются инженерным или
научным свидетельством и не устанавливают эквивалентность ответа или
превосходство стоимости в рабочей среде.

```text
qwake_qw_lc3_repository_freeze_merged=true
qwake_qw_lc3_repository_freeze_complete=true
qwake_qw_lc3_complete=true
qwake_qw_lc4_i_authoring_open=true
qwake_qw_lc4_i_implementation_materialized=true
qwake_qw_lc4_i_implementation_id=stage3b-qwake-lc4-i-bounded-implementation-v1
qwake_qw_lc4_i_implementation_sha256=sha256:4dc7b123e2af3a09d675550e52aff361146a744bcf5b4717b426137d44b88dfa
qwake_qw_lc4_i_implementation_registry_sha256=sha256:f1ca469d3aeb3fe5c4a90f6bdb068a61444bf9b8eb0efe25b29121821c990894
qwake_qw_lc4_i_complete=false
qwake_qw_lc4_f_branch_permitted=false
qwake_bounded_analytic_candidate_materialized=true
qwake_complete_exact_suffix_materialized=true
qwake_opaque_state_ref_implementation_materialized=true
qwake_rng_restoration_implementation_materialized=true
qwake_required_response_mapper_materialized=true
qwake_resource_cost_mapper_materialized=true
qwake_paired_aggregation_materialized=true
qwake_synthetic_unit_test_only=true
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
qwake_next_slice=QW-LC4-I-merge
qwake_post_merge_next_slice=QW-LC4-F
```

## `QW-LC4-F`: authoring рабочей фиксации материализован

Ограниченная реализация `QW-LC4-I` слита через PR №123 в `main`
`c9f3dadcd5330887584b8bf71d906c667dacf076` и независимо проверена. Authoring
пакет `stage3b-qwake-lc4-f-runtime-freeze-authoring-v1` материализует runtime
frontier adapter, deny-all preflight, точную схему одной инженерной
authorization и sealing boundary без runtime executor.

Отдельный запрос фиксирует две полосы, индексы кандидата `0..6`, двенадцать
повторов на каждую комбинацию и два точных reserve probes. Матрица содержит 14
runtime cells, 168 matched-pair cells и 28 reserve probes. Ничего из этого в
текущем срезе не выполнялось.

Фактический image digest ещё не зафиксирован: сначала authoring-срез должен быть
закоммичен, затем образ должен быть построен из этого точного коммита. Поэтому
сам runtime-freeze и `QW-LC4-E` остаются закрыты.

```text
qwake_qw_lc4_i_merged=true
qwake_qw_lc4_i_complete=true
qwake_qw_lc4_i_merge_commit=c9f3dadcd5330887584b8bf71d906c667dacf076
qwake_qw_lc4_f_authoring_open=true
qwake_qw_lc4_f_authoring_materialized=true
qwake_qw_lc4_f_authoring_id=stage3b-qwake-lc4-f-runtime-freeze-authoring-v1
qwake_qw_lc4_f_authoring_sha256=sha256:c0a11996708b091e737a0bfa60e2a000f65b9e9f0971e8c3041838f25922860a
qwake_qw_lc4_f_authoring_registry_sha256=sha256:a59af6fe70612277ceaecba9a86a2dc49dcb2612154993d9c7cc10d8c3bcb7f4
qwake_qw_lc4_f_request_frozen=true
qwake_qw_lc4_f_request_id=stage3b-qwake-lc4-f-runtime-freeze-request-v1
qwake_qw_lc4_f_request_sha256=sha256:bc4e36f9265837dc0a36f0eca039b057a5113c4ef872f72e1698db5bc4930506
qwake_qw_lc4_f_request_registry_sha256=sha256:0a58be97a03c7283cf1b46e5815e7ca58271b4b61a29cd53566fa6d7600212ea
qwake_qw_lc4_f_runtime_module_sha256=sha256:003759e0eac5062e34b0ead1f24c1e1babb09f096023539ac3303a2af9957a7c
qwake_qw_lc4_f_adapter_registry_sha256=sha256:40397474de6c97663ac44c718d4c52846a4ba077bc5343a0d10114afd576bbde
qwake_qw_lc4_f_runtime_cell_count=14
qwake_qw_lc4_f_matched_pair_count=168
qwake_qw_lc4_f_reserve_probe_count=28
qwake_qw_lc4_f_materialized=false
qwake_qw_lc4_f_complete=false
qwake_qw_lc4_e_branch_permitted=false
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
qwake_next_slice=QW-LC4-F-authoring-commit
qwake_post_commit_next_slice=QW-LC4-F-runtime-materialization
```

Текущее состояние является только подготовкой проверяемой рабочей границы.
Оно не подтверждает результат вычисления и не создаёт эмпирического
свидетельства. Переход к следующему действию допустим лишь после отдельной
проверки неизменяемого исходного коммита, образа, внешнего checkout и полного
набора квитанций. Любой преждевременный запуск должен завершаться отказом и не
может учитываться в исследовании.
## `QW-LC4-F`: рабочая фиксация материализована

См. [ADR-063](docs/decisions/ADR-063-stage3b-qwake-lc4-f-runtime-freeze.md).

Точный коммит авторинга связан с образом, проверками CPU/ROCm, цепочкой из
22 статических проверок, одноразовым разрешением и десятифайловым пакетом
`stage3b-qwake-lc4-f-runtime-freeze-v1`.

Разрешение не означает исполнения. До слияния и независимой проверки после
слияния `QW-LC4-F` незавершён, `QW-LC4-E` запрещён, а научные и
публикационные возможности закрыты.

```text
qwake_adr=ADR-063-stage3b-qwake-lc4-f-runtime-freeze
qwake_source_commit=51fc7537fdcb395145fc4c5a38b8918b018fe892
qwake_image_digest=sha256:a31cf96e20ab45ce29fe18b68eb805bd048a02f1f8107cf680d1c174ea363929
qwake_preflight_sha256=sha256:3a8d7817338f3b93396270ea8e1b1b2fbda768dbd5461a18f97520948a53a9e6
qwake_authorization_sha256=sha256:d11b662a5c5eeada5333e69c6fddf2e50726c01b4d8c78a556a68167dbdd301e
qwake_next_slice=QW-LC4-F-merge
qwake_post_merge_next_slice=QW-LC4-E
QW_LC4_F_MATERIALIZED=true
QW_LC4_F_COMPLETE=false
QW_LC4_E_BRANCH_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
```
## `QW-LC4-E`: авторинг допуска материализован

См. [ADR-064](docs/decisions/ADR-064-stage3b-qwake-lc4-e-execution-admission-authoring.md).

Добавлены чистая схема и валидатор будущего одноразового допуска. Они проверяют
точный пакет `QW-LC4-F`, подтверждение оператора и отсутствие каталога
результатов и файла владения. Исполнитель модели и запись допуска отсутствуют.

```text
qwake_adr=ADR-064-stage3b-qwake-lc4-e-execution-admission-authoring
QW_LC4_F_COMPLETE=true
QW_LC4_E_BRANCH_OPEN=true
EXECUTION_ADMISSION_IMPLEMENTED=true
EXECUTION_ADMISSION_ISSUED=false
QW_LC4_E_EXECUTION_PERMITTED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```
## `QW-LC4-E`: конкретный допуск зафиксирован

См. [ADR-065](docs/decisions/ADR-065-stage3b-qwake-lc4-e-execution-admission-freeze.md).

Пятифайловый пакет связан с `main` `bce821dff0729629db0ccb306d8f3fd1dd9a2e13`. Запись допуска разрешает одну
инженерную попытку, но файл владения, исполнитель и каталог результатов отсутствуют.
Веточный gate выполнения остаётся закрытым.

```text
qwake_adr=ADR-065-stage3b-qwake-lc4-e-execution-admission-freeze
qwake_admission_sha256=sha256:d1ee6d022588f0a2cf0ac23f3bf8de9b27f9aad4fc1153435bd70e1ab83e296c
qwake_admission_file_sha256=sha256:d819f8a7e03314242c0072e2d020a59fbe6b7f6984fda99ff0dcd306cc97ca70
qwake_admission_receipt_sha256=sha256:d4b9d33117cbf522b1c62173c7a81f9638cde703eb6b3bbb392ff46e45a17c25
qwake_admission_package_registry_sha256=sha256:411f3e8d62b367755a6f02070ad84bc6f37cfefad602d885674a844b57aa74cd
QW_LC4_E_AUTHORING_MERGED=true
ADMISSION_FREEZE_BRANCH_OPEN=true
ADMISSION_FREEZE_MATERIALIZED=true
EXECUTION_ADMISSION_ISSUED=true
ADMISSION_RECORD_RUNTIME_EXECUTION_PERMITTED=true
QW_LC4_E_EXECUTION_PERMITTED=false
AUTHORIZATION_CONSUMED=false
EXECUTION_LEASE_PRESENT=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```
## `QW-LC4-E`: проектирование владения и исполняющей обёртки

См. [ADR-066](docs/decisions/ADR-066-stage3b-qwake-lc4-e-execution-lease-wrapper-authoring.md).

Срез проверяет слитую запись допуска, предварительную одноразовую запись
владения и будущий контракт исполняющей обёртки только в памяти. Программы
записи владения и результатов и исполнитель рабочей среды отсутствуют.

```text
qwake_adr=ADR-066-stage3b-qwake-lc4-e-execution-lease-wrapper-authoring
qwake_lease_test_vector_sha256=sha256:66961a641d7f9cc9b7b2f958c432a492c1ada171056b827136171dd0df2b355a
qwake_wrapper_contract_test_vector_sha256=sha256:0ff0cf0b0f23bf21d65567079212e5bad04e16e257815143d3f581664fa4dbf0
ADMISSION_FREEZE_MERGED=true
EXECUTION_LEASE_WRAPPER_AUTHORING_BRANCH_OPEN=true
EXECUTION_LEASE_SCHEMA_IMPLEMENTED=true
EXECUTION_WRAPPER_CONTRACT_IMPLEMENTED=true
EXECUTION_LEASE_MATERIALIZED=false
EXECUTION_LEASE_WRITER_PRESENT=false
RUNTIME_EXECUTOR_PRESENT=false
RESULT_WRITER_PRESENT=false
QW_LC4_E_EXECUTION_PERMITTED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

### Пояснение к состоянию управления выполнением

Настоящий этап описывает исключительно проверяемые правила будущего запуска.
Он не создаёт файл владения, не потребляет разрешение и не вызывает модельное
вычисление. Отдельная реализация должна сохранить исключительность одной
попытки, атомарность переходов, неизменность исходных данных и закрытое
состояние при любой ошибке. До независимой проверки реализации запуск,
формирование результатов и публикация свидетельств остаются запрещёнными.

## `QW-LC4-E`: атомарная реализация владения и исполняющей обёртки

См. [ADR-067](docs/decisions/ADR-067-stage3b-qwake-lc4-e-execution-lease-wrapper-implementation.md).

Атомарная реализация добавлена отдельным модулем после слияния и независимой
проверки проектирования. Он умеет создать файл владения через временный файл,
синхронизацию и исключительную жёсткую ссылку, повторно проверить отсутствие
каталога результата после захвата, выполнить внедрённый backend только во
временном каталоге и продвинуть полный результат через
`renameat2(RENAME_NOREPLACE)`.

Реализация сохраняет файл владения после любой ошибки и запрещает повторную
попытку. Неполный временный каталог удаляется, чужой каталог результата никогда
не заменяется, символические ссылки и нерегулярные файлы отклоняются. Проверка
механики выполняется только в одноразовом каталоге `/tmp`; в репозитории файл
владения и результат не создаются.

Наличие программы записи и исполнителя не открывает выполнение. Ветка всё ещё
не содержит команды фактического запуска, неизменяемой фиксации точного коммита
реализации или разрешения на потребление допуска. До отдельной фиксации
выполнения любое применение эффектов запрещено и не является инженерным
свидетельством `QW-LC4-E`.

```text
qwake_adr=ADR-067-stage3b-qwake-lc4-e-execution-lease-wrapper-implementation
qwake_implementation_json_sha256=sha256:f7cb2c72f5e9516d808f8f76802e2e560579f407aa1e155675bae2570a09b08e
qwake_implementation_registry_sha256=sha256:348b574bf7093edd4db263779014c256209a38b1c9e4c78f9598d0f82bf8b59a
LEASE_WRAPPER_AUTHORING_MERGED=true
LEASE_WRAPPER_IMPLEMENTATION_BRANCH_OPEN=true
LEASE_WRAPPER_IMPLEMENTATION_MATERIALIZED=true
EXECUTION_LEASE_SCHEMA_IMPLEMENTED=true
EXECUTION_WRAPPER_CONTRACT_IMPLEMENTED=true
EXECUTION_LEASE_WRITER_PRESENT=true
RUNTIME_EXECUTOR_PRESENT=true
RESULT_WRITER_PRESENT=true
EXECUTION_LEASE_MATERIALIZED=false
QW_LC4_E_EXECUTION_PERMITTED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```
## `QW-LC4-E`: авторинг фиксации выполнения

См. [ADR-068](docs/decisions/ADR-068-stage3b-qwake-lc4-e-execution-freeze-authoring.md).

PR №128 слит в `main` `24966cd2a0380e46ab1924ff4ab8987f17e1fe9e`;
точный implementation tree и CI независимо подтверждены. Новый чистый
контракт связывает это состояние с замороженным допуском и формирует
детерминированный execution-freeze request.

Проверка выявила обязательную незавершённость: generic wrapper существует, но
конкретный backend для получения реальных FixedPred frontier states и
одноразовая команда вызова отсутствуют. Поэтому неизменяемый образ выполнения,
фиксация выполнения и разрешение запуска остаются закрытыми.

```text
qwake_adr=ADR-068-stage3b-qwake-lc4-e-execution-freeze-authoring
qwake_execution_freeze_request_sha256=sha256:9b28943043082efe96fb313f94875ef18c7f8e7361d8c0eb1b8c140e82a1e312
qwake_authoring_json_sha256=sha256:9dfe3177442abdbe255047732a33d02d0987e4d634f0b1c629e1671fc68677dd
qwake_authoring_registry_sha256=sha256:9b65ba87c817fa67670ab4e225f15e9b1f2544459439cda2e5e0b621b324ca53
LEASE_WRAPPER_IMPLEMENTATION_MERGED=true
EXECUTION_FREEZE_BRANCH_OPEN=true
EXECUTION_FREEZE_CONTRACT_MATERIALIZED=true
CONCRETE_RUNTIME_BACKEND_PRESENT=false
ONE_SHOT_ENTRYPOINT_PRESENT=false
IMMUTABLE_EXECUTION_IMAGE_PRESENT=false
EXECUTION_FREEZE_MATERIALIZED=false
EXECUTION_LEASE_MATERIALIZED=false
QW_LC4_E_EXECUTION_PERMITTED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: ограниченный runtime backend

См. [ADR-069](docs/decisions/ADR-069-stage3b-qwake-lc4-e-runtime-backend-implementation.md).

Отдельный срез материализует конкретный backend для замороженной синтетической
матрицы `2 × 7 × 12`, 28 точных резервных зондов и одноразовую точку входа.
Backend не читает набор данных и не выполняется при импорте. Будущая команда
сначала обязана проверить точный пакет `execution-freeze-v1`, commit Torch2PC,
SHA-256 кода и digest неизменяемого образа; пока пакет отсутствует, она
останавливается до захвата файла владения.

Для реальных frontier `lenet_classic` зафиксирована чистая канонизация только
уже завершённых верхних ошибок `fixed - beliefs` в пределах строгого допуска.
Исходный и канонический frontier имеют отдельные SHA-256. Превышение допуска
закрывает попытку. Отрицательные эмпирические результаты `~R`, ГПСЧ,
резервного пути или эффекта порядка сохраняются как инженерное свидетельство,
а не приводят к потере staging после одноразового допуска.

```text
qwake_adr=ADR-069-stage3b-qwake-lc4-e-runtime-backend-implementation
RUNTIME_BACKEND_BRANCH_OPEN=true
CONCRETE_RUNTIME_BACKEND_PRESENT=true
ONE_SHOT_ENTRYPOINT_PRESENT=true
RUNTIME_EXECUTION_FREEZE_GUARD_PRESENT=true
FRONTIER_ROUNDOFF_CANONICALIZATION_PRESENT=true
NEGATIVE_VALIDATION_EVIDENCE_PRESERVED=true
IMMUTABLE_EXECUTION_IMAGE_PRESENT=false
EXECUTION_FREEZE_MATERIALIZED=false
EXECUTION_LEASE_MATERIALIZED=false
QW_LC4_E_EXECUTION_PERMITTED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

### Материализация фиксации выполнения `QW-LC4-E`

См. [ADR-070](docs/decisions/ADR-070-stage3b-qwake-lc4-e-execution-freeze-materialization.md).

- PR №130 слит в `main` `67a084c0b970ad79ad0692442f660085a73b080a` и независимо проверен;
- из этого коммита построен неизменяемый образ `torch2pc-layerwise-thesis:0.1.0-qw-lc4-e-freeze-67a084c0b970` с идентификатором `sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d`;
- девятифайловый пакет `execution-freeze-v1` связывает образ, вычислительный модуль, точку входа, допуск и авторизацию;
- исходный `image-build.log` сохраняется байт-в-байт и точечно классифицируется в `.gitattributes` как двоичное запечатанное свидетельство;
- внутренняя запись разрешает будущую одноразовую точку входа, но веточный допуск выполнения остаётся закрытым;
- файл владения, каталог результата, инженерные материалы, научное выполнение, тестовая выборка и публикация отсутствуют.

## `QW-LC4-E`: разрешение одноразового инженерного вызова

См. [ADR-071](docs/decisions/ADR-071-stage3b-qwake-lc4-e-one-shot-invocation-authorization.md).

После проверенного слияния PR №131 материализован отдельный машиночитаемый
пакет разрешения. Он связывает точные идентичности неизменяемого образа,
`execution-freeze-v1`, допуска, матричной авторизации, вычислительного модуля, обёртки и точки
входа. Внутренняя запись разрешает один будущий инженерный вызов и один будущий
захват файла владения.

Разрешение не является выполнением. На ветке не создан файл владения, отсутствуют
каталог результата и подготовительный каталог, авторизация не потреблена, модель не вызывалась.

```text
qwake_adr=ADR-071-stage3b-qwake-lc4-e-one-shot-invocation-authorization
qwake_invocation_authorization_sha256=sha256:0a60dacc1bfd5073cf52d76f2ec33ae54f00899aad9877d44607199659fda75a
qwake_invocation_authorization_registry_sha256=sha256:9a47f79e9607db98a2c7c224c25cbeee920974d4c339eef4ef82d4f9aa7c8f83
ONE_SHOT_INVOCATION_AUTHORIZED=true
FUTURE_LEASE_CLAIM_AUTHORIZED=true
FUTURE_RUNTIME_EXECUTION_AUTHORIZED=true
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: авторинг хостовой обёртки одноразового вызова

См. [ADR-072](docs/decisions/ADR-072-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-authoring.md).

После проверки PR №132 после слияния отдельный чистый модуль фиксирует будущую
хостовую границу вызова. Контракт требует точный `image repo digest`, проверку
исходной метки образа, отключённую сеть, корневую файловую систему только для
чтения и отдельную временную файловую систему `/tmp`. Разрешены ровно три
монтирования каталогов, устройства `/dev/kfd` и `/dev/dri`, явный пользователь,
дополнительные группы и зафиксированные входы ограничений ресурсов. Исходное
дерево проекта и набор данных монтировать запрещено.

Текущий срез не содержит `subprocess`, вызова Docker или материализованной
команды. Он только повторно проверяет разрешение и строит канонический контракт
будущего вызова во временной памяти.

```text
qwake_adr=ADR-072-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-authoring
qwake_invocation_wrapper_contract_sha256=sha256:4c4cb163e8c2a33b0563cc3b9cb873a87acf8ea75bb3e807d157d51c5a4dd29b
INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
INVOCATION_WRAPPER_AUTHORING_BRANCH_OPEN=true
INVOCATION_WRAPPER_CONTRACT_PRESENT=true
CONTAINER_COMMAND_TEMPLATE_PRESENT=true
GPU_DEVICE_BINDING_COUNT=2
TMPFS_REQUIRED=true
TMPFS_TARGET=/tmp
HOST_RUNTIME_INVOKER_PRESENT=false
IMAGE_INSPECTION_IMPLEMENTED=false
INVOCATION_COMMAND_MATERIALIZED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: реализация хостовой обёртки одноразового вызова

См. [ADR-073](docs/decisions/ADR-073-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-implementation.md).

После проверки PR №133 после слияния отдельный модуль реализует точную проверку
локального неизменяемого образа. Единственная внешняя операция —
`docker image inspect` точного `image repo digest`; тег, `image ID`, все слои,
исходная метка, переменная `SOURCE_GIT_COMMIT`, точка входа и рабочий каталог
сверяются с пакетом `execution-freeze-v1`.

Будущий вызов материализуется только как канонический кортеж `argv` в памяти.
Он запрещает загрузку образа, сеть, привилегированный режим, лишние возможности,
исходное дерево и [набор данных](docs/glossary.md#term-dataset). Команда не
сохраняется и не исполняется.

```text
qwake_adr=ADR-073-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-implementation
IMAGE_INSPECTION_IMPLEMENTED=true
INVOCATION_COMMAND_MATERIALIZED=true
INVOCATION_COMMAND_PERSISTED=false
HOST_RUNTIME_INVOKER_PRESENT=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: авторинг одноразового хостового исполнителя

См. [ADR-074](docs/decisions/ADR-074-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-authoring.md).

После проверки PR №134 после слияния отдельный чистый контракт связывает
реализацию канонического `argv` с единственной будущей попыткой container spawn.
Хост повторно проверяет образ и команду, но не записывает execution lease:
атомарный захват остаётся обязанностью контейнерной точки входа в том же
процессе, который затем выполняет вычислительный модуль.

Контракт фиксирует запрет оболочки, один дочерний процесс, отсутствие
автоматического повтора после spawn, тайм-аут, пересылку сигналов, ограниченный
захват вывода и сохранение lease после ошибки. Сам исполнитель отсутствует.

```text
qwake_adr=ADR-074-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-authoring
HOST_RUNTIME_INVOKER_CONTRACT_PRESENT=true
HOST_RUNTIME_INVOKER_PRESENT=false
HOST_RUNTIME_INVOKER_EXECUTABLE=false
HOST_DOCKER_RUN_IMPLEMENTED=false
EXACT_ARGV_ONLY=true
SHELL_INTERPRETATION_FORBIDDEN=true
EXECUTION_ATTEMPT_LIMIT=1
HOST_EXECUTION_LEASE_WRITE_FORBIDDEN=true
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: реализация одноразового хостового исполнителя

См. [ADR-075](docs/decisions/ADR-075-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-implementation.md).

После проверки PR №135 после слияния реализован ограниченный хостовый исполнитель. Он дважды проверяет образ и канонический `argv`, создаёт не более одного дочернего процесса без оболочки, использует отдельную группу процессов, пересылает сигналы, применяет терминальный тайм-аут и ограничивает вывод. Проверяющая программа не вызывает исполнитель, а тесты используют только поддельный процесс.

```text
qwake_adr=ADR-075-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-implementation
HOST_RUNTIME_INVOKER_IMPLEMENTATION_PRESENT=true
HOST_RUNTIME_INVOKER_PRESENT=true
HOST_RUNTIME_INVOKER_EXECUTABLE=true
HOST_DOCKER_RUN_IMPLEMENTED=true
PRELAUNCH_IMAGE_INSPECTION_COUNT=2
PRELAUNCH_MATERIALIZATION_COUNT=2
SUBPROCESS_POPEN_CALL_LIMIT=1
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: фиксация состояния репозитория хостового исполнителя материализована

См. [ADR-076](docs/decisions/ADR-076-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-repository-freeze.md).

После независимой проверки слияния PR №136 материализована двухфайловая
квитанция, связывающая точный merge commit, оба родителя, исправленную
герметичную проверку, хэши реализации и ревизию Torch2PC. Этот срез не вызывает
исполнитель, не проверяет локальный образ и не создаёт файл владения или
результат. Заморозка останется незавершённой до слияния квитанции и повторной
проверки.

```text
qwake_adr=ADR-076-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-repository-freeze
qwake_host_runtime_invoker_repository_main_commit=da51c8d858c541372525125640db99062041fc20
qwake_host_runtime_invoker_implementation_head=181abda36465d3a91db5970e684938266200a798
qwake_host_runtime_invoker_repository_freeze_materialized=true
qwake_host_runtime_invoker_repository_freeze_complete=false
qwake_next_slice=QW-LC4-E-one-shot-host-runtime-invoker-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC4-E-one-shot-engineering-invocation
HOST_RUNTIME_INVOKER_IMPLEMENTATION_PRESENT=true
HOST_RUNTIME_INVOKER_PRESENT=true
HOST_RUNTIME_INVOKER_EXECUTABLE=true
HOST_DOCKER_RUN_IMPLEMENTED=true
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
IMAGE_INSPECTION_PERFORMED=false
DOCKER_RUN_PERFORMED=false
RUNTIME_RERUN_PERFORMED=false
FILES_STAGED=false
```

## `QW-LC4-E`: допуск одноразового инженерного вызова материализован

См. [ADR-077](docs/decisions/ADR-077-stage3b-qwake-lc4-e-one-shot-engineering-invocation-admission.md).

После независимой проверки слияния PR №137 материализован чистый допуск,
связывающий точную фиксацию репозитория, ранее выданную одноразовую авторизацию,
неизменяемый образ и ограниченный хостовый исполнитель. Проверка рабочей среды
и сам вызов остаются отдельной операцией; этот срез не выполняет image
inspection, `docker run`, захват файла владения или запись результата.

```text
qwake_adr=ADR-077-stage3b-qwake-lc4-e-one-shot-engineering-invocation-admission
qwake_invocation_base_commit=3454d12d3cc16c9c50977e2a598e2bc1a8768441
qwake_invocation_admission_sha256=sha256:fe07bc20bf5866d84730df945c2ababc7b5f4f255648c5de6e3185ba4e37c01d
REPOSITORY_FREEZE_COMPLETE=true
INVOCATION_ADMISSION_RECORD_PRESENT=true
PREEXECUTION_IDENTITY_CHECKS_IMPLEMENTED=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
IMAGE_INSPECTION_PERFORMED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: запись операции одноразового инженерного вызова материализована

См. [ADR-078](docs/decisions/ADR-078-stage3b-qwake-lc4-e-one-shot-engineering-invocation-operation.md).

После независимой проверки слияния PR №138 материализована чистая запись
операции. Она связывает merge commit допуска, авторизацию, образ, Torch2PC и
ограниченный хостовый исполнитель, а также фиксирует точные динамические
проверки будущего запуска. Этот срез не выполняет image inspection, не
материализует команду, не создаёт `lease` и не вызывает `docker run`.

```text
qwake_adr=ADR-078-stage3b-qwake-lc4-e-one-shot-engineering-invocation-operation
qwake_operation_base_commit=28be77706bc86abaf34f86e9bdcbdcb9cc2810a8
qwake_invocation_operation_sha256=sha256:10a612ef1b765362b361ecea57923d00a9f7339c9d3f9e3b27337f92f15326e9
REPOSITORY_FREEZE_COMPLETE=true
INVOCATION_ADMISSION_COMPLETE=true
INVOCATION_OPERATION_RECORD_PRESENT=true
PREEXECUTION_IDENTITY_CHECKS_IMPLEMENTED=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_OPERATION_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: авторизация выполнения одноразового инженерного вызова материализована

См. [ADR-079](docs/decisions/ADR-079-stage3b-qwake-lc4-e-one-shot-engineering-invocation-execution-authorization.md).

После независимой проверки слияния PR №139 материализована чистая авторизация
одного будущего вызова. Она связывает коммит слияния операции, прежнюю
одноразовую авторизацию, образ, Torch2PC и ограниченный хостовый исполнитель и
фиксирует обязательную проверку перед выполнением в рамках одного процесса. Подготовительная ветка не
выполняет image inspection, не материализует команду, не создаёт `lease` и не
вызывает `docker run`.

```text
qwake_adr=ADR-079-stage3b-qwake-lc4-e-one-shot-engineering-invocation-execution-authorization
qwake_execution_base_commit=b0f6729e8fd1cb1aa172eef488dc56e36b335173
qwake_execution_authorization_sha256=sha256:ff136538faee0d7952dc444e521d7ec760c7d54cd38406cb9b19ff1e00d9437b
REPOSITORY_FREEZE_COMPLETE=true
INVOCATION_ADMISSION_COMPLETE=true
INVOCATION_OPERATION_COMPLETE=true
EXECUTION_AUTHORIZATION_RECORD_PRESENT=true
EXECUTION_AUTHORIZATION_ISSUED=true
PREEXECUTION_VERIFICATION_MATERIALIZATION_IMPLEMENTED=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_OPERATION_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_EXECUTION_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: контракт проверки перед одноразовым инженерным вызовом материализован

См. [ADR-080](docs/decisions/ADR-080-stage3b-qwake-lc4-e-one-shot-engineering-invocation-preexecution-verification.md).

После независимой проверки слияния PR №140 материализован чистый контракт
проверки перед выполнением. Он связывает коммит слияния авторизации с точной
реализацией хостового исполнителя и фиксирует, что обе проверки образа, обе
материализации команды и единственное создание дочернего процесса относятся к
одному будущему вызову. Текущая ветка не выполняет динамическую проверку образа,
не материализует команду, не создаёт `lease` и не вызывает `docker run`.

```text
qwake_adr=ADR-080-stage3b-qwake-lc4-e-one-shot-engineering-invocation-preexecution-verification
qwake_preexecution_base_commit=49c4b97e93b47cefbf35576736927ece02c9402b
qwake_preexecution_verification_sha256=sha256:833371b427a5c8a6e602d675711b85b2edc68441b9e5be191321a2911bce6128
INVOCATION_OPERATION_COMPLETE=true
EXECUTION_AUTHORIZATION_COMPLETE=true
PREEXECUTION_VERIFICATION_RECORD_PRESENT=true
PREEXECUTION_VERIFIER_IMPLEMENTED=true
PREEXECUTION_STATIC_CONTRACT_VERIFIED=true
PREEXECUTION_VERIFICATION_SLICE_OPEN=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_EXECUTION_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_OPEN=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: ограниченная операция одноразового инженерного вызова материализована

См. [ADR-081](docs/decisions/ADR-081-stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation.md).

После независимой проверки слияния PR №141 материализован чистый контракт
атомарной операции и ограниченная точка входа. Она требует явное разрешение,
точное подтверждение, время после слияния, прежнее подтверждение авторизации и
полный набор ресурсов хоста. Динамическая проверка и единственное создание дочернего процесса
делегируются существующему хостовому исполнителю; authoring-ветка не инспектирует
образ, не материализует команду, не создаёт `lease` и не вызывает Docker.

```text
qwake_adr=ADR-081-stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation
qwake_runtime_operation_base_commit=494e6a0b2f10c26b49c90fbb84c23565699a4064
qwake_runtime_operation_sha256=sha256:0332428014f7f8385c789ba7e7c55d6c2ec03b020e3f83df9ac9714483bb6bf8
EXECUTION_AUTHORIZATION_COMPLETE=true
PREEXECUTION_VERIFICATION_COMPLETE=true
PREEXECUTION_STATIC_CONTRACT_VERIFIED=true
RUNTIME_OPERATION_RECORD_PRESENT=true
RUNTIME_OPERATION_EXECUTOR_ENTRYPOINT_IMPLEMENTED=true
RUNTIME_OPERATION_STATIC_CONTRACT_VERIFIED=true
ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_OPEN=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## QW-LC4-E: восстановление идентичности операции рабочей среды

- PR №142 слит в `main` коммитом `97dacb207aa201f1fd2f43c66ae34b1adced32bb`;
- обнаружено, что исторический ADR-081 сохранил SHA модуля до исправления Ruff, а двухфайловый пакет не связывал исполняемый исходный код;
- ADR-082 добавляет не ретроактивный пакет восстановления идентичности и обязательную проверку собственной идентичности модуля;
- исторический ADR-081 и пакет v1 не переписываются;
- выполнение остаётся заблокированным до повторной полной проверки, слияния исправления, постоянного файла владения v2 и устойчивой квитанции отрицательного исхода;
- `ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false`, `DOCKER_RUN_PERFORMED=false`.

## `QW-LC4-E`: постоянная доказательная цепочка v2 материализована как authoring-контракт

См. [ADR-083](docs/decisions/ADR-083-stage3b-qwake-lc4-e-persistent-evidence-chain-v2.md).

PR №143 слит коммитом `5e61ed650c9beda2cde1f58650345f01694836f6` и
независимо проверен: `24` focused, `201` targeted и `1248` полных тестов.
Authoring-пакет связывает полную актуальную цепочку авторизаций и операций в
шаблоне persistent lease v2 и определяет обязательную устойчивую квитанцию
терминального host outcome. Запись обоих артефактов и lease-bound wiring ещё не
реализованы; выполнение остаётся закрытым.

```text
qwake_adr=ADR-083-stage3b-qwake-lc4-e-persistent-evidence-chain-v2
qwake_persistent_evidence_chain_v2_base=5e61ed650c9beda2cde1f58650345f01694836f6
qwake_persistent_evidence_chain_v2_sha256=sha256:c0a6195080cec64e6104a90076366cc2bfa10a723b45a7389cd77fa1b3b11bd1
CORRECTED_FULL_VALIDATION_RECEIPT_PRESENT=true
RUNTIME_OPERATION_IDENTITY_REPAIR_MERGED=true
LATEST_AUTHORIZATION_BOUND_IN_PERSISTENT_LEASE_TEMPLATE=true
DURABLE_NEGATIVE_HOST_OUTCOME_DEFINED=true
PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=false
DURABLE_OUTCOME_WRITER_IMPLEMENTED=false
LEASE_BOUND_HOST_INVOKER_ENFORCED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: реализована запись постоянной доказательной цепочки v2

См. [ADR-084](docs/decisions/ADR-084-stage3b-qwake-lc4-e-persistent-evidence-chain-v2-implementation.md).

От merge PR №144 `3d092440b0314f02072c9773cc91018bf2860744`
реализованы закрытые при ошибке интерфейсы записи для постоянного файла
владения v2 и устойчивого терминального исхода хоста. Реализация обеспечивает эксклюзивность без перезаписи, режим `0600`,
file/directory `fsync`, запрет символьных родительских каталогов, очистку временного файла и
проверку точных канонических байтов файла владения перед outcome. Подключение к исполнителю хоста и
выполнение не открыты.

```text
PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=true
DURABLE_OUTCOME_WRITER_IMPLEMENTED=true
LEASE_BOUND_HOST_INVOKER_ENFORCED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: исполнитель хоста привязан к постоянному файлу владения v2

См. [ADR-085](docs/decisions/ADR-085-stage3b-qwake-lc4-e-lease-bound-host-invoker-wiring.md). Новый перспективный вход проверяет точные сохранённые байты файла владения v2 до обращения к исполнителю, запрещает повтор и формирует устойчивую терминальную квитанцию. Историческая прямая операция сохранена неизменной, но заменена для будущей авторизации.

```text
LEASE_BOUND_HOST_INVOKER_ENFORCED=true
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_EXECUTION_PERFORMED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
FILES_STAGED=false
```

## `QW-LC4-E`: подготовка финального подтверждения выполнения

См. [ADR-086](docs/decisions/ADR-086-stage3b-qwake-lc4-e-final-execution-acknowledgement-authoring.md).

После независимой проверки слияния PR №146 на
`2957d8f6975c88e7bdb23243e3915c7f51d4ba47` отдельный статический пакет
подготовки связывает доказательную цепочку v2, её реализацию, привязанный к
файлу владения исполнитель, авторизации, точный образ, Torch2PC, каталог
результатов и `invocation_count=1`. Будущее подтверждение требует точную фразу
`ACKNOWLEDGE_QWAKE_LC4_FINAL_ONE_SHOT_EXECUTION`, идентичность оператора и время
по всемирному координированному времени после слияния. Пакет не выпускает подтверждение и не выполняет переход к
файлу владения или запуску.

```text
qwake_adr=ADR-086-stage3b-qwake-lc4-e-final-execution-acknowledgement-authoring
qwake_acknowledgement_authoring_base=2957d8f6975c88e7bdb23243e3915c7f51d4ba47
wiring_pr=146
wiring_focused_tests=39
wiring_targeted_tests=240
wiring_full_tests=1287
wiring_full_test_warnings=14
FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```


## `QW-LC4-E`: подготовка выпуска финального подтверждения

См. [ADR-087](docs/decisions/ADR-087-stage3b-qwake-lc4-e-final-execution-acknowledgement-issuance-authoring.md).

После независимой проверки слияния PR №147 на
`eb20c157584efff8e9aa0418385242c7d7b26eab` статический контракт выпуска
связывает точный пакет ADR-086 с единственным будущим путём подтверждения,
оператором, выпускающим, двумя временами по всемирному координированному
времени и атомарной записью без перезаписи. Программа записи и само
подтверждение отсутствуют; файл владения и выполнение остаются закрытыми.

```text
acknowledgement_authoring_pr=147
acknowledgement_authoring_focused_tests=50
acknowledgement_authoring_targeted_tests=251
acknowledgement_authoring_full_tests=1298
acknowledgement_authoring_full_test_warnings=14
ACKNOWLEDGEMENT_ISSUANCE_CONTRACT_AUTHORED=true
ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTED=false
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

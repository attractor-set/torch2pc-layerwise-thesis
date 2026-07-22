# Статус исследования

[English version](STATUS_EN.md)

На 22 июля 2026 года опубликованы неизменяемые результаты Stage 1/2, Stage 3A,
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

ADR-035 сохраняет post-publication исследовательское направление: oracle-поиск
минимального достаточного вычислительного агрегата на двух масштабах.
Конкретные пространственные membership и snapshot-ветвление должны быть
зафиксированы следующим контрактом; spike-like динамика не входит в критический
путь.

```text
recursive_sufficiency_direction_frozen=true
ex_if0_protocol_frozen=true
exact_implementation_candidate=stage2_baseline
minimum_sufficient_sweep_rule_frozen=true
recursive_aggregate_execution_open=false
global_policy_action=false
spike_like_on_critical_path=false
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

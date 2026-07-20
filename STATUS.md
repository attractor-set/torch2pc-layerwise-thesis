# Статус исследования

[English version](STATUS_EN.md)

На 20 июля 2026 года опубликованы неизменяемые результаты Stage 1/2, Stage 3A,
Stage 3B B0, `SI-MA0` и `SI-MA1`. Завершены предварительная регистрация и реализация точных кандидатов B1 и B2.
Подтверждающий B1 запечатан на 120/120 парах; B2 прошёл инженерный smoke на
12 тройках и 24 сравнениях. Подтверждающий B2 предварительно зарегистрирован; его fail-closed opening-инфраструктура реализована, но выполнение закрыто. Ранее сформированные артефакты открытия
[сопоставленного профилирования](docs/glossary.md#term-matched-profiling)
сохраняются, однако production prelaunch блокирует их до confirmatory B2.

Полный Stage 3B остаётся незавершённым.

## Машинно-проверяемая граница текущего состояния

```text
matched_profiling_manifest_cells=288
scientific_admission=blocked_pending_eq_b2_confirmatory
candidate_aware_runner=complete
b2_confirmatory_opening=implementation_ready_execution_closed
b2_confirmatory_request_frozen=false
matched_profiling_request_refresh_required=true
runtime_authorization=not_issued
measurements_allowed=false
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
| B2 `composite_vjp` | engineering smoke `EQ-B2=pass`; 12/12 троек и 24/24 сравнения; confirmatory opening-инфраструктура готова, request не заморожен, execution закрыт |
| Запрос и манифест сопоставленного профилирования | прежняя версия сохранена; production refresh требуется после confirmatory B2 |
| Исполнитель сопоставленного профилирования | реализация с учётом кандидата завершена |
| Выполнение сопоставленного профилирования | не разрешено |
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
B2 прошёл инженерный smoke на 12/12 тройках и 24/24 сравнениях. Smoke
`EQ-B2=pass` не является confirmatory admission и не открывает production
matched profiling. Для допуска требуются `EQ-B2-CONFIRMATORY`, derived
`EQ-B2` и новая версионированная фиксация request/manifest.

## Текущий переход

Подтверждающий B2 предварительно зарегистрирован как 120 matched triples и
240 прямых сравнений на тех же десяти validation batches, что и confirmatory
B1. Fail-closed opening-инфраструктура реализована со статусом
`implementation_ready_execution_closed`. Следующий незавершённый шаг —
отдельная prospective фиксация request. Только после неё допускаются сборка
immutable image, lane preflight, authorization и неизмеряемый dry-run.

До положительного sealed `EQ-B2-CONFIRMATORY`, derived admission `EQ-B2` и
новой фиксации matched-profiling request/manifest:

```text
scientific_admission=blocked_pending_eq_b2_confirmatory
runtime_authorization=not_issued
measurements_allowed=false
```

Документационное обновление не разрешает B2 execution, 288-cell campaign,
`EX-IF0`, `A11-OFF0`, `A11-OFF1`, predictor, QWake-PC или test split.

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

Документационные изменения не пересоздают опубликованные результаты.

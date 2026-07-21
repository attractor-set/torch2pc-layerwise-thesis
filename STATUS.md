# Статус исследования

[English version](STATUS_EN.md)

На 20 июля 2026 года опубликованы неизменяемые результаты Stage 1/2, Stage 3A,
Stage 3B B0, `SI-MA0` и `SI-MA1`. Завершены предварительная регистрация и реализация точных кандидатов B1 и B2.
Подтверждающий B1 запечатан на 120/120 парах. Подтверждающий B2 также
завершён и запечатан: 120/120 троек, 240/240 прямых сравнений, все пять gates
прошли, failed pairs отсутствуют; производный admission `EQ-B2` сохранён.
Исторические артефакты открытия
[сопоставленного профилирования](docs/glossary.md#term-matched-profiling)
сохранены byte-for-byte. Новый пакет `v2` prospectively привязан к sealed
admissions B1/B2 и прошёл научный prelaunch gate; runtime authorization и
измерения всё ещё не разрешены.

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
| B2 `composite_vjp` | `EQ-B2-CONFIRMATORY=pass`; 120/120 троек, 240/240 сравнений, 0 failed pairs; derived `EQ-B2` сохранён |
| Запрос и манифест сопоставленного профилирования | новый `v2` refreeze сохранён; исторический `v1` неизменен |
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
B2 прошёл инженерный smoke, а затем подтверждающую кампанию на 120/120
тройках и 240/240 прямых сравнениях. `EQ-B2-CONFIRMATORY=pass` запечатан;
derived `EQ-B2` связан с ним SHA-256. Эта научная цепочка допуска завершена,
но production matched profiling остаётся закрытым до новой версионированной
фиксации request/manifest и отдельной runtime authorization.

## Текущий переход

Запечатанный набор B2 опубликован в
`results/stage-3/b2/stage3b-b2-confirmatory-63885e5-v1/`. Он содержит
`EQ-B2-CONFIRMATORY=pass`, derived `EQ-B2`, 120 завершённых append-only
историй, агрегированные метрики и 1800 структурных событий. Test split не
использовался.

Новый версионированный `v2` freeze 288-cell matched-profiling request/manifest
сохранён в `experiments/frozen/stage3b-matched-profiling-v2/` и prospectively
ссылается на запечатанные admissions B1 и B2. Прежний `v1` request/manifest
сохранён byte-for-byte и не получает допуска задним числом. Следующий шаг —
отдельные immutable image, ROCm preflight, runtime authorization и dry-run gates.

До отдельной проверки runtime:

```text
scientific_admission=open
matched_profiling_request_refrozen=true
matched_profiling_request_refresh_required=false
matched_profiling_execution_open=false
runtime_authorization=not_issued
measurements_allowed=false
```

Документационное обновление и сохранение evidence не разрешают 288-cell
campaign, `EX-IF0`, `A11-OFF0`, `A11-OFF1`, predictor, QWake-PC или test split.

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

Документационные изменения не пересоздают опубликованные результаты.

# Torch2PC Layer-wise Thesis

[English version](README_EN.md)

![Python](https://img.shields.io/badge/Python-3.12-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.9.1-ee4c2c)
![ROCm](https://img.shields.io/badge/ROCm-7.2.1-ED1C24)
![Лицензия](https://img.shields.io/badge/код-Apache--2.0-green)
![Статус](https://img.shields.io/badge/этап-EQ--B1%2FEQ--B2%20sealed%3B%20matched%20profiling%20open-blue)

Репозиторий магистерской диссертации по сравнению обратного распространения
ошибки (backpropagation, BP) и режимов предиктивного кодирования в Torch2PC.
Проект отделяет предположения от наблюдений, процедуры от результатов, а
результаты — от их интерпретации.

Нормативные определения и русско-английские соответствия терминов:
[глоссарий исследования](docs/glossary.md).

## Исследовательская позиция

Проект следует нейтральной исследовательской позиции:

- превосходство метода не предполагается заранее;
- теоретические ожидания формулируются как проверяемые предположения;
- отсутствие обнаруженного различия не считается эквивалентностью без
  отдельного анализа эквивалентности;
- эмпирическое утверждение принимается только в пределах заранее описанного
  эксперимента и зафиксированной вычислительной среды;
- отрицательные, смешанные и нестабильные результаты сохраняются;
- выводы ограничиваются исследованной реализацией, архитектурами, наборами
  данных и вычислительной средой.

Подробно: [RESEARCH_PRINCIPLES.md](RESEARCH_PRINCIPLES.md).

## Исследовательский вопрос

При каких алгоритмических и вычислительных условиях режимы `Exact`,
`FixedPred` и `Strict` дают результаты, близкие к BP, и когда различия выходят
за заранее заданные численные или статистические границы?

После завершения Stage 3A и B0 основной post-B0 вопрос уточнён:

> Можно ли построить вычислительно экономичное диагностическое представление
> `state_inference`, достаточное для безопасного выбора числа последующих
> полных exact sweeps?

Верхнеуровневая рамка — [PC-TREF](docs/pc-tref-balanced-core.md), механизмная
модель — [PC-CATM](docs/pc-catm-operator-model.md), реалистичный маршрут —
[Scenario A](docs/stage3b-primary-scenario-a.md).

Сравнение охватывает:

- корректность реализации и численные контрольные соотношения;
- качество классификации;
- послойные градиенты;
- нейронные представления;
- устойчивость к искажениям;
- вычислительное время и память;
- воспроизводимость между независимыми запусками.

## Текущее состояние на 17 июля 2026 года

В закреплённой среде Ubuntu/ROCm завершены:

- пилотная кампания: **96/96**, тестовая выборка не использовалась;
- Stage 1: **80/80** на исходном Torch2PC
  `00c6c50ee3540537bbb56ab2b6567b541f42b093`;
- Stage 2: **80/80** на изменённом Torch2PC
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- Stage 3A: послойная диагностика, model-level statistics, анализ по глубине и
  публикационные рисунки;
- Stage 3B B0: каноническая базовая линия ROCm/float32, 96/96 ячеек и
  опубликованный статистический и инженерный анализ;
- `SI-MA0`: механизмная реконструкция, observer non-interference и version
  coherence прошли, но исходный `COST-MA0` не прошёл из-за медианного
  accounting residual около `0.1606`;
- `SI-MA1`: десять `model_seed`, 180 matched blocks, observer-calibrated
  `CAL-COST-MA1` и итоговый `SI-MA1` прошли;
- теоретический пакет `PC-TREF`/`PC-CATM` фиксирует operational proximity,
  regret-based required equivalence, norm contracts и раздельные cost
  boundaries перед B1/B2.
- B1 `isolated_layer_vjp` и B2 `composite_vjp` реализованы; их CPU `float64`
  и ROCm `float32` smoke evidence агрегированы в положительные sealed решения
  `EQ-B1` и `EQ-B2`;
- научный допуск к общему B0/B1/B2 matched profiling открыт; измерения и
  отдельная runtime authorization ещё не выполнялись.

Stage 3A, B0, `SI-MA0` и `SI-MA1` не обращались к test split. Raw и sealed
результаты не переписываются документационными обновлениями. Актуальное
состояние регрессионных проверок фиксирует CI; документация не закрепляет
быстро устаревающее число пройденных тестов.

Подробный статус: [STATUS.md](STATUS.md). Последовательность дальнейшей работы:
[ROADMAP.md](ROADMAP.md).

## Основные опубликованные результаты

### Stage 1 и Stage 2

Изменения Stage 2 сохранили экспериментальный протокол и изменили только
вычислительный путь. По среднему общему времени обучения относительно Stage 1:

- Exact выполнялся примерно на 14% быстрее;
- FixedPred — примерно на 31% быстрее;
- Strict — примерно на 26% быстрее;
- время BP практически не изменилось.

Наблюдаемый порядок времени Stage 2:
`BP ≈ Exact < FixedPred << Strict`.

Парные записи опубликованы в
[`results/cross-version/`](results/cross-version/).

### Stage 3A

Подтверждающая кампания охватывает FashionMNIST, `lenet_classic` и случайные
начальные значения 0–9. Опубликованы:

- 2250 наблюдений градиентов;
- 150 наблюдений CKA/RSA по представлениям;
- 750 наблюдений межслойного CKA;
- 40 подтверждающих сравнений градиентов;
- 20 подтверждающих сравнений представлений;
- 24 статистические строки анализа по глубине;
- 8 PDF-рисунков.

В зарегистрированной области `FixedPred` почти сохраняет направление градиента,
но существенно уменьшает его норму в ранних слоях. `Strict` в скрытых слоях
отличается от BP по направлению и масштабу. Представления `FixedPred` ближе к
BP, чем представления `Strict`.

Подробный отчёт:
[docs/stage3a-statistical-results.md](docs/stage3a-statistical-results.md).

### Stage 3B B0

B0 закрепляет кандидата `stage2_baseline` для `FixedPred` и `Strict` в
синтетической кампании масштабирования ROCm/float32. Канонический протокол
использует 20 разогревочных шагов, 5 повторений и 50 измеряемых шагов.

Завершены:

- 96/96 канонических ячеек и 96/96 попыток;
- 0 неудачных попыток и 0 системных отказов ресурсов;
- 96 записей процессов и 96 уникальных дочерних PID;
- 48 ячеек `FixedPred` и 48 ячеек `Strict`;
- 96 строк по ячейкам, 480 по областям, 48 парных и 32 по конфигурациям;
- измерение областей `initial_forward`, `state_inference`, `local_state_vjp`,
  `parameter_vjp` и `optimizer_step`;
- проверки отсутствия возмущения, полноты и конечности значений.

Зафиксированные доказательные материалы:
[`results/stage-3/profiling/b0/sealed-v1/`](results/stage-3/profiling/b0/sealed-v1/).
Контрольная сумма набора:
`6a3d61838810e559a39f13e6ac39d6b22624c21d72523bddb55c33e83063c93e`.

Инженерный анализ опубликован в
[`results/stage-3/profiling/b0/analysis-v1/`](results/stage-3/profiling/b0/analysis-v1/).
Независимая статистическая единица — отдельно обученная модель, заданная
`model_seed`; доступны три модели на конфигурацию.

Основные выводы в зарегистрированной области:

- медианное отношение Strict/FixedPred для времени на устройстве — **2.327×**;
- медианное отношение пиковой выделенной памяти — **1.328×**;
- основная область времени — вывод состояний (`state_inference`);
- отношение сохранённых тензоров Strict/FixedPred в `state_inference` —
  **11.998×**.

Эти результаты являются описательным инженерным анализом закреплённой матрицы,
а не универсальным ранжированием методов. Полный Stage 3B остаётся
незавершённым:
`full_stage3b_campaign_complete=false`.

### Stage 3B `SI-MA0` и `SI-MA1`

`SI-MA0` выполнил зарегистрированные mechanism-attribution checks на десяти
независимо обученных моделях. `REC-MA0`, `OBS-MA0`, `VER-MA0` и `CMP-MA0`
прошли, но `COST-MA0` не прошёл: медианный непокрытый accounting residual
составил примерно `0.1606`. Этот результат сохранён как отрицательный и не
переписывается.

`SI-MA1` проверил отдельную observer calibration с matched A/B/C blocks и
signed residual:

- `10` model seeds и `180` matched blocks;
- observed median `D_seed = -0.190635073373`;
- one-sided 95% bootstrap upper bound `-0.188621876160`;
- registered threshold `0.01`;
- `CAL-COST-MA1=true`, `si_ma1_passed=true`.

Отрицательный `D_seed` означает over-closure калибровки, а не отрицательную
физическую стоимость. `SI-MA1` не включает `ECZ` evaluator, action selection,
fallback validation или end-to-end B1/B2 benefit. Итоговые материалы:
[`results/stage-3/si-ma1/confirmatory/`](results/stage-3/si-ma1/confirmatory/).

Теоретическое предварительное условие B1/B2 закрывается
[теоретическим пакетом](docs/pc-tref-pc-catm-theoretical-foundation.md) и
[ADR-013](docs/decisions/ADR-013-pc-tref-operational-semantics.md).

## Цепочка выполнения и публикации

| Роль | Идентификатор |
|---|---|
| Исходное состояние Stage 1 | `140e77cc2083bf04234dcea16b95803e63cb0537` |
| Источник выполнения Stage 2 | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Публикационное состояние Stage 2 | `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| Тег публикации Stage 3A | `stage3a-statistical-publication-v1` |
| Источник выполнения Stage 3B B0 | `95c25d35224abd5e741f1df9327662ff2fde23ad` |
| Источник фиксации целостности Stage 3B B0 | `caa226cc1cd5d4aa0f9772c1fb997f7388d60730` |
| Публикационное состояние Stage 3B B0 | `ed0d48063a17e2d9c6679869a4d930f933877052` |
| Тег доказательных материалов Stage 3B B0 | `stage3b-b0-evidence-v1` |
| Реализация анализа Stage 3B B0 | `e7a1632a947fae578e877826f0c923342669430e` |
| Публикационное состояние анализа Stage 3B B0 | `b9ff8b2ab76f8752b15dd3bb968565d05f1fe9d3` |
| Тег анализа Stage 3B B0 | `stage3b-b0-analysis-evidence-v1` |
| Предварительная регистрация `SI-MA1` | `stage3b-si-ma1-prereg-v1` |
| Тег реализации `SI-MA1` | `stage3b-si-ma1-implementation-v1` |
| Тег выполнения `SI-MA1` | `stage3b-si-ma1-confirmatory-execution-v1` |
| Итоговый тег `SI-MA1` | `stage3b-si-ma1-confirmatory-v1` |
| Публикационное состояние итогового `SI-MA1` | `9bf500a2494267e83cbf9657ad2f075e349a8a75` |

Выпуски GitHub:

- [`stage2-results-v1`](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage2-results-v1)
- [`stage3b-b0-evidence-v1`](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage3b-b0-evidence-v1)
- [`stage3b-b0-analysis-evidence-v1`](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage3b-b0-analysis-evidence-v1)

## Следующий этап

Положительные sealed `EQ-B1` и `EQ-B2` выполнили зарегистрированное условие
открытия общего matched profiling. Текущий slice фиксирует 288-cell B0/B1/B2
matrix и машиночитаемый request без выполнения измерений:
[matched profiling opening](experiments/planned/STAGE3B-B1-B2-MATCHED-PROFILING.md).

Следующий разрешённый шаг — candidate-aware matched runner и отдельная
ROCm/float32 runtime freeze. `EX-IF0`, estimator, active `ECZ`, `QWake-PC`,
controller actions, offline policy selection и test split остаются закрытыми.

## Контрольные проверки

Обозначения C0 и C1 используются вместо H0/H1, чтобы не смешивать технические
контроли с нулевыми статистическими гипотезами.

- **C0:** численное сопоставление градиентов `Exact` и BP;
- **C1:** численное сопоставление `FixedPred` при `eta=1`, `n>=depth` и `Exact`;
- **структурная проверка:** проверка выбранных выражений Torch2PC, связанных с
  поправкой Rosenbaum 2025.

Успешный результат C0/C1 относится только к закреплённым версии кода, типу
данных, устройству и тестовым пакетам. Он не является универсальным
доказательством эквивалентности алгоритмов.

## Воспроизведение

Базовая подготовка среды:

```bash
cp .env.example .env
./scripts/setup_ubuntu.sh
make init
make host-check
make image-check
make pin-base-image
make build
make validate
make prepare
```

`make pin-base-image` заменяет изменяемый тег Docker на неизменяемую ссылку
`repository@sha256:...`. Локальный `.env` не добавляется в Git.

Дальнейшие команды и требования к фиксации среды описаны в
[docs/reproducibility.md](docs/reproducibility.md) и
[docs/validation.md](docs/validation.md).

## Защита тестовой выборки

- стадии `smoke` и `pilot` не создают загрузчик тестовой выборки;
- тестовая выборка разрешена только для стадии `final`;
- `final` требует замороженного протокола и артефакта `pilot-freeze`;
- каждый запуск сохраняет разрешённую конфигурацию, описание среды, контрольные
  суммы разбиений, предсказания по примерам, метрики и уникальный `run_id`;
- повторный успешный запуск той же комбинации кода, конфигурации и начального
  значения блокируется, чтобы повторный просмотр тестовой выборки не считался
  новой репликацией.

## Структура репозитория

| Каталог | Назначение |
|---|---|
| `src/torch2pc_thesis/` | Исполняемая исследовательская логика и CLI |
| `configs/` | Базовые, аппаратные, этапные и методические конфигурации |
| `experiments/` | Добавляемый реестр запусков и планы экспериментов |
| `results/` | Агрегированные публичные материалы |
| `notebooks/analysis/` | Анализ зарегистрированных результатов |
| `notebooks/legacy/` | Исторический блокнот для проверки миграции |
| `thesis/` | Русскоязычный каркас диссертации |
| `article/` | Англоязычный каркас статьи с суффиксом `_EN` |
| `references/` | BibTeX и матрица литературы без PDF |
| `docs/` | Протоколы, решения и журнал исследования |

Полная схема: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

## Язык и терминология

Русский является основным языком пользовательских материалов. Английские
версии используют суффикс `_EN`. Технические идентификаторы Python, YAML,
Torch2PC и GitHub сохраняются на английском. Канонические термины определены в
[LANGUAGE_POLICY.md](LANGUAGE_POLICY.md).

## Лицензирование

- программный код: Apache License 2.0 — [LICENSE](LICENSE);
- текст диссертации, статьи, документации, таблицы и рисунки: Creative Commons
  Attribution 4.0 International — [LICENSE-DOCS](LICENSE-DOCS) и
  [LICENSE-DOCS_EN](LICENSE-DOCS_EN);
- сторонние материалы сохраняют исходные лицензии и условия атрибуции —
  [NOTICE](NOTICE) и [NOTICE_EN](NOTICE_EN).

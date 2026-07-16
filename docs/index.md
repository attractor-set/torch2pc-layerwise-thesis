# Документация исследования

[English version](index_EN.md)

Документация связывает исследовательский вопрос, протокол,
[выполнение](glossary.md#term-execution),
[доказательные материалы](glossary.md#term-evidence) и выводы в
зарегистрированной области. Планы отделяются от наблюдений, а опубликованные
результаты сопровождаются границами утверждений и происхождением артефактов.

## Текущее состояние

На 16 июля 2026 года:

- `Stage` 1/2, `Stage` 3A и `Stage` 3B B0 завершены и опубликованы;
- `SI-MA0` завершён с сохранённым отрицательным `COST-MA0`;
- `SI-MA1` завершён на десяти `model_seed` и прошёл `CAL-COST-MA1`;
- итоговый тег — `stage3b-si-ma1-confirmatory-v1`;
- [теоретическое основание `PC-TREF`/`PC-CATM`](pc-tref-pc-catm-theoretical-foundation.md)
  фиксирует операциональную семантику до B1/B2;
- предварительная регистрация B1/B2 разрешается после публикации этого пакета;
- реализация, подтверждающее выполнение, `EX-IF0`, `passive` `diagnostics`,
  `predictor`, `QWake-PC` и `final` `test` остаются будущей работой;
- `full_stage3b_campaign_complete=false` и `test` `split` закрыт.

`SI-MA1` не переписывает `SI-MA0`: первый `observer-calibrated` эксперимент
устранил положительный непокрытый `residual` в зарегистрированном одностороннем
правиле, но не измерял стоимость будущего `ECZ` `evaluator` или управляющего
контура.

## Как читать документацию

1. [Текущий статус](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/STATUS.md)
   содержит подтверждённое состояние и границы выводов.
2. [Дорожная карта](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/ROADMAP.md)
   определяет разрешённую последовательность дальнейшей работы.
3. [Глоссарий](glossary.md) задаёт нормативные значения терминов и русско-
   английские соответствия.
4. Протоколы и предварительные регистрации задают правила до выполнения.
5. Каталоги результатов и отчёты фиксируют наблюдения после выполнения.
6. [Языковая политика](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/LANGUAGE_POLICY.md)
   требует синхронных русской и английской версий.

## Основные документы

### Сквозные правила

- [Глоссарий исследования](glossary.md)
- [Языковая и терминологическая политика](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/LANGUAGE_POLICY.md)
- [Принципы исследования](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/RESEARCH_PRINCIPLES.md)

### Исследовательская постановка

- [Исследовательский вопрос](research-question.md)
- [Методология](methodology.md)
- [План анализа](analysis-plan.md)
- [Экспериментальный протокол](experiment-protocol.md)
- [Воспроизводимость](reproducibility.md)
- [Управление данными](data-management.md)
- [Аппаратная среда](hardware.md)

### `PC-TREF`, `PC-CATM` и `Scenario` A

- [Теоретическое основание после `SI-MA1`](pc-tref-pc-catm-theoretical-foundation.md)
- [PC-TREF Balanced Core](pc-tref-balanced-core.md)
- [PC-CATM коррекционного нуля и переноса ошибки](pc-catm-operator-model.md)
- [Основной рабочий сценарий A](glossary.md#term-primary-working-scenario) ([документ](stage3b-primary-scenario-a.md))
- [Реалистичный план магистерской диссертации](masters-thesis-plan.md)
- [ADR-013: операциональная семантика и допуск B1/B2](decisions/ADR-013-pc-tref-operational-semantics.md)

### Этапы и результаты

- [Протокол этапа 2](stage-2-protocol.md)
- [Протокол этапа 3](stage-3-protocol.md)
- [Готовность этапа 3](stage-3-readiness.md)
- [Статистические результаты этапа 3A](stage3a-statistical-results.md)
- [Проверка и фиксация целостности Stage 3B B0](glossary.md#term-integrity-sealing) ([документ](stage3b-b0-sealing.md))
- [Конвейер анализа Stage 3B B0](stage3b-b0-analysis-pipeline.md)
- [Зафиксированные доказательные материалы B0](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/main/results/stage-3/profiling/b0/sealed-v1)
- [Инженерный анализ B0](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/main/results/stage-3/profiling/b0/analysis-v1)
- [`SI-MA1` confirmatory evidence](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/main/results/stage-3/si-ma1/confirmatory)
- [`SI-MA1` итоговый отчёт](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/results/stage-3/si-ma1/confirmatory/si_ma1_report.md)
- [`SI-MA1` итоговый тег](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/stage3b-si-ma1-confirmatory-v1)

### Научные и архитектурные решения

- [Индекс ADR](decisions/index.md)

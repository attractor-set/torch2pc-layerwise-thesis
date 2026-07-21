# Документация исследования

[English version](index_EN.md)

Документация связывает исследовательский вопрос, протокол,
[выполнение](glossary.md#term-execution),
[доказательные материалы](glossary.md#term-evidence) и выводы в
зарегистрированной области. Планы отделяются от наблюдений, а опубликованные
результаты сопровождаются границами утверждений и происхождением артефактов.

## Текущее состояние

На 21 июля 2026 года:

- этапы 1/2, 3A, 3B B0, `SI-MA0` и `SI-MA1` завершены;
- подтверждающие B1 и B2 запечатаны с положительными решениями `EQ-B1` и
  `EQ-B2`;
- 288-ячеечное [сопоставленное профилирование](glossary.md#term-matched-profiling)
  выполнено полностью: 288/288 ячеек, 96/96 блоков, 0 сбоев;
- [доказательные материалы](glossary.md#term-evidence) сохранены в репозитории и связаны с неизменяемым тегом
  `stage3b-matched-profiling-evidence-v1`;
- полный набор из десяти артефактов запуска загружен в проверенный черновой
  релиз;
- протокол описательного анализа после сбора и до анализа зафиксирован как
  `stage3b-matched-descriptive-analysis-protocol-v1`;
- реализация анализа разрешена отдельным `PR`, но выполнение на запечатанных доказательных материалах,
  публикация, `EX-IF0`, политика и тестовая выборка остаются закрытыми;
- `full_stage3b_campaign_complete=false`.

Фиксация протокола выполнена после сбора данных и поэтому не называется
предварительной регистрацией до сбора. Она закрывает аналитические степени
свободы до вычисления сравнительных результатов.

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
- [Протокол описательного анализа сопоставленного профилирования](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/experiments/planned/STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS.md)
- [Запечатанные доказательные материалы сопоставленного профилирования](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/main/results/stage-3/profiling/matched/stage3b-matched-profiling-e1dcfb2-v1)

### Научные и архитектурные решения

- [Индекс ADR](decisions/index.md)

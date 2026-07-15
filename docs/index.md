# Документация исследования

[English version](index_EN.md)

Документация связывает исследовательский вопрос, протокол, [выполнение](glossary.md#term-execution),
[доказательные материалы](glossary.md#term-evidence) и выводы в зарегистрированной области. Планы не
смешиваются с наблюдениями, а опубликованные результаты всегда сопровождаются
областью применимости и происхождением артефактов.

## Текущее состояние

- этапы 1 и 2 завершены и опубликованы как неизменяемые базовые линии;
- диагностика и статистическая публикация этапа 3A завершены;
- каноническое [выполнение](glossary.md#term-execution), проверка, [фиксация целостности](glossary.md#term-integrity-sealing) и публикация базовой
  линии этапа 3B B0 завершены;
- статистический и инженерный анализ этапа 3B B0 завершён и опубликован;
- полный этап 3B остаётся незавершённым;
- [основной рабочий сценарий](glossary.md#term-primary-working-scenario) A принят после B0; его `design-only` фиксация завершена, а следующий фактический этап — проверки `shortcut` и наблюдателя.

Машинная граница состояния сохраняется без перевода:
`full_stage3b_campaign_complete=false`.

## Как читать документацию

1. [Текущий статус](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/STATUS.md)
   содержит только подтверждённое состояние и границы выводов.
2. [Дорожная карта](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/ROADMAP.md)
   описывает последовательность дальнейшей работы и условия перехода.
3. Протоколы и предварительная регистрация задают правила до выполнения.
4. Каталоги результатов и отчёты фиксируют наблюдения после выполнения.
5. [Глоссарий исследования](glossary.md) фиксирует значения терминов и их
   русско-английскую эквивалентность. Первое содержательное употребление
   канонического термина в документе связывается с соответствующей статьёй
   глоссария.
6. [Языковая и терминологическая политика](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/LANGUAGE_POLICY.md)
   задаёт порядок выбора, добавления и изменения терминов.

## Основные документы

### Сквозные правила

- [Глоссарий исследования](glossary.md)
- [Языковая и терминологическая политика](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/LANGUAGE_POLICY.md)

### Исследовательская постановка

- [Исследовательский вопрос](research-question.md)
- [Методология](methodology.md)
- [План анализа](analysis-plan.md)
- [Экспериментальный протокол](experiment-protocol.md)
- [Воспроизводимость](reproducibility.md)
- [Управление данными](data-management.md)
- [Аппаратная среда](hardware.md)

### `PC-TREF`, `PC-CATM` и основной сценарий

- [Реалистичный план магистерской диссертации](masters-thesis-plan.md)

- [PC-TREF Balanced Core](pc-tref-balanced-core.md)
- [PC-CATM коррекционного нуля и переноса ошибки](pc-catm-operator-model.md)
- [План сценария A](stage3b-primary-scenario-a.md)

### Этапы и результаты

- [Протокол этапа 2](stage-2-protocol.md)
- [Протокол этапа 3](stage-3-protocol.md)
- [Готовность этапа 3](stage-3-readiness.md)
- [Статистические результаты этапа 3A](stage3a-statistical-results.md)
- [Проверка и фиксация целостности этапа 3B B0](stage3b-b0-sealing.md)
- [Конвейер анализа этапа 3B B0](stage3b-b0-analysis-pipeline.md)
- [Зафиксированные доказательные материалы этапа 3B B0](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/main/results/stage-3/profiling/b0/sealed-v1)
- [Инженерный анализ этапа 3B B0](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/main/results/stage-3/profiling/b0/analysis-v1)
- [Отчёт анализа этапа 3B B0](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/results/stage-3/profiling/b0/analysis-v1/report.md)
- [Выпуск анализа этапа 3B B0](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage3b-b0-analysis-evidence-v1)

### Архитектурные решения

- [Индекс ADR](decisions/index.md)

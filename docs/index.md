# Документация исследования

[English version](index_EN.md)

Документация связывает исследовательский вопрос, протокол, выполнение,
доказательные материалы и ограниченные выводы. Планы не смешиваются с
наблюдениями, а опубликованные результаты всегда сопровождаются областью
применимости и происхождением артефактов.

## Текущее состояние

- этапы Stage 1 и Stage 2 завершены и опубликованы как неизменяемые базовые
  линии;
- диагностика и статистическая публикация Stage 3A завершены;
- каноническое выполнение, проверка, фиксация целостности и публикация базовой
  линии Stage 3B B0 завершены;
- статистический и инженерный анализ Stage 3B B0 завершён и опубликован;
- полный этап Stage 3B остаётся незавершённым;
- следующий этап — проверки численной эквивалентности для кандидатов B1 и B2.

Машинная граница состояния сохраняется без перевода:
`full_stage3b_campaign_complete=false`.

## Как читать документацию

1. [Текущий статус](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/STATUS.md)
   содержит только подтверждённое состояние и границы выводов.
2. [Дорожная карта](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/ROADMAP.md)
   описывает последовательность дальнейшей работы и условия перехода.
3. Протоколы и предварительная регистрация задают правила до выполнения.
4. Каталоги результатов и отчёты фиксируют наблюдения после выполнения.
5. [Глоссарий исследования](glossary.md) фиксирует значения терминов и
   их русско-английскую эквивалентность.
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

### Этапы и результаты

- [Протокол Stage 2](stage-2-protocol.md)
- [Протокол Stage 3](stage-3-protocol.md)
- [Готовность Stage 3](stage-3-readiness.md)
- [Статистические результаты Stage 3A](stage3a-statistical-results.md)
- [Проверка и фиксация целостности Stage 3B B0](stage3b-b0-sealing.md)
- [Конвейер анализа Stage 3B B0](stage3b-b0-analysis-pipeline.md)
- [Зафиксированные доказательные материалы Stage 3B B0](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/main/results/stage-3/profiling/b0/sealed-v1)
- [Инженерный анализ Stage 3B B0](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/main/results/stage-3/profiling/b0/analysis-v1)
- [Отчёт анализа Stage 3B B0](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/main/results/stage-3/profiling/b0/analysis-v1/report.md)
- [Выпуск анализа Stage 3B B0](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage3b-b0-analysis-evidence-v1)

### Архитектурные решения

- [Индекс ADR](decisions/index.md)

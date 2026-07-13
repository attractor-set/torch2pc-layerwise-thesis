# ADR-006: границы расширенного Stage 3

[English version](ADR-006-stage3-scope_EN.md)

- Статус: принято для проектирования
- Дата: 2026-07-13
- Момент принятия: после завершения и публикации Stage 2, до реализации Stage 3

## Контекст

Stage 2 сохранил качество и уменьшил runtime всех PC режимов, но остаточный
порядок времени остался `BP ≈ Exact < FixedPred << Strict`. У проекта остаётся
один год до завершения магистерской диссертации. Простое продолжение
implementation tuning имеет ограниченную научную добавленную ценность.

## Решение

Stage 3 исследует три связанные оси:

1. математическая и execution locality;
2. точные implementation-preserving способы организации VJP;
3. контролируемые аппроксимации: adaptive stopping и periodic VJP refresh.

Fixed random feedback сохраняется как условный exploratory track. Mixed
precision, quantization, surrogate derivatives, asynchronous inference и
`torch.compile` не входят в core scope v1.

Stage 3 не повторяет Stage 1/2. Он использует их опубликованные состояния как
historical baseline и создаёт собственную provenance chain.

## Последствия

- core scope остаётся выполнимым в годовом горизонте;
- точные и approximate claims не смешиваются;
- diagnostics executor становится обязательным инфраструктурным результатом;
- final test остаётся закрытым до отдельного Stage 3 freeze;
- отрицательный результат по кандидату сохраняет научную ценность через
  profiling, locality и scaling observations.

# STAGE3-001: локальность, аппроксимация и масштабирование

[English version](STAGE3-001_EN.md)

## Статус

Design-ready; execution blocked.

## Baseline

- Stage 2 execution: `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2`;
- Stage 2 publication: `bb435432a65b76b7fc4f383b566b9a372fc346ae`;
- Torch2PC: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

## Матрицы

- profiling: 336 коротких matched cells;
- core screening pilot: 48 parameterized validation-only terminal cells;
- predict-correct screening: 27 validation-only terminal cells;
- final template: до 80 cells после freeze.

## Acceptance для начала реализации

- `make stage3-ready` проходит;
- deterministic plan формируется;
- Stage 3 отсутствует из `TRAINING_STAGES`;
- final template сохраняет test выключенным.


## Научная граница

План различает изменение способа исполнения точных формул и изменение самого
алгоритмического приближения. Первый случай требует численного сопоставления с
закреплённой реализацией, второй — оценки качества, устойчивости и согласования
градиентов без заявления о точном совпадении.

# Статус исследования

[English version](STATUS_EN.md)

Stage 1 и Stage 2 завершены и сохраняются как неизменяемая опубликованная
базовая линия. Текущий активный этап — подготовка расширенного Stage 3 по
локальности, аппроксимации и масштабированию.

| Компонент | Наблюдаемый статус |
|---|---|
| Validation-only pilot | 96/96 terminal-ячеек, 0 failed, test не вычислялся |
| Stage 1 final | 80/80 completed, 0 failed |
| Stage 2 final | 80/80 completed, 0 failed |
| Модель и данные Stage 1/2 | `lenet_classic`, MNIST и FashionMNIST |
| Исходный Torch2PC | `00c6c50ee3540537bbb56ab2b6567b541f42b093` |
| Patched Torch2PC | `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |
| Stage 2 execution source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Stage 2 results state | `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| CPU/GPU equivalence gates Stage 2 | Пройдены |
| Regression suite после Stage 3 scaffold | 82 passed |
| Stage 1 / Stage 2 quality | Парные test accuracy и macro-F1 совпали |
| Производительность Stage 2 | `BP ≈ Exact < FixedPred << Strict` |
| Public release | Завершён 13 июля 2026 года |
| Stage 3 design | `ready_for_stage3_implementation` |
| Stage 3 execution | Заблокирован до candidates, gates и freeze |

## Stage 3 readiness

Репозиторий содержит:

- подробный протокол Stage 3 и два ADR;
- design contract `configs/stage3/design.yaml`;
- отдельные profiling, pilot и final-template конфигурации;
- locality trace schema и profiling contract;
- MLP family для depth/width scaling;
- deterministic design plan: 288 profiling и 48 parameterized validation-only screening cells;
- CLI/Make checks, сохраняющие Stage 3 вне `TRAINING_STAGES`;
- final template с `evaluation.use_test=false`.

Проверка:

```bash
make stage3-ready
make stage3-plan
```

## Следующий шаг

Реализовать non-perturbing B0 profiler executor и получить baseline locality
report. Затем по отдельности реализовать B1 isolated VJP и B2 composite VJP,
провести CPU/GPU equivalence gates и только после этого переходить к C1/C2.

Stage 1/2 не повторяются. Любой код Stage 3 получает отдельный commit,
environment lock, execution tag и results/publication state.

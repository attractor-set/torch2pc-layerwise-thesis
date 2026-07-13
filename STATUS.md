# Статус исследования

[English version](STATUS_EN.md)

Состояние после завершения двух подтверждающих 80-ячеечных серий. Stage 1
использует исходный Torch2PC, Stage 2 — закреплённый implementation-preserving
patch. Численные контроли ограничены закреплённой экспериментальной областью и
не трактуются как универсальное доказательство для любых моделей и сред.

| Компонент | Наблюдаемый статус |
|---|---|
| Validation-only pilot | 96/96 terminal-ячеек, 0 failed, test не вычислялся |
| Stage 1 final | 80/80 completed, 0 failed |
| Stage 2 final | 80/80 completed, 0 failed |
| Модель и данные | `lenet_classic`, MNIST и FashionMNIST |
| Исходный Torch2PC | `00c6c50ee3540537bbb56ab2b6567b541f42b093` |
| Patched Torch2PC | `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |
| Stage 2 execution source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| CPU/GPU equivalence gates | Пройдены |
| Stage 1 / Stage 2 quality | Парные значения test accuracy и macro-F1 совпали |
| Производительность Stage 2 | Exact ≈ BP; FixedPred и Strict существенно ускорены |
| Cross-version analysis | Создан в `results/cross-version/` |
| Torch2PC equivalence audit | `docs/torch2pc-patched-v1-equivalence.md` |
| Подтверждающие результаты | Сформированы и готовы к описанию в диссертации |

## Текущая задача

Завершить post-experiment maintenance: стабилизировать CSV-хэши, пересоздать
Stage 2 manifest с правильным environment lock, проверить CI и подготовить
полный replication bundle с raw run artifacts.

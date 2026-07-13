# Статус исследования

[English version](STATUS_EN.md)

Stage 1/2 завершены и остаются неизменяемой опубликованной базовой линией.
Диагностическая подкампания **Stage 3A layer-wise diagnostics** завершена;
расширенные линии locality, profiling и acceleration продолжаются отдельно.

| Компонент | Наблюдаемый статус |
|---|---|
| Validation-only pilot | 96/96; test не вычислялся |
| Stage 1 / Stage 2 | 80/80 и 80/80 |
| Stage 2 runtime | `BP ≈ Exact < FixedPred << Strict` |
| Stage 3A same-state probes | 10/10 seeds |
| Stage 3A representation probes | 10/10 seeds |
| Exact–BP numerical controls | 10/10 passed |
| Gradient observations | 2250; cosine определён для 2250/2250 |
| Representation observations | 150; RSA определён для 150/150 |
| Cross-layer CKA observations | 750 |
| Regression suite | 94 passed |
| Test access Stage 3A | validation-only diagnostics; test loader не создавался |
| Расширенный Stage 3 | profiling, locality, exact candidates и approximations ожидают отдельных gates |

## Текущая интерпретация

Stage 3A сформировал подтверждающий послойный evidence-набор для финальных
FashionMNIST checkpoints `lenet_classic`, seeds 0–9. Статистической единицей
остаётся независимо обученная модель; слои, batches и samples являются
повторными наблюдениями внутри seed.

## Следующий шаг

Выполнить парный seed-level статистический анализ, Holm-коррекцию, оценку
эффектов и построение графиков. После публикации Stage 3A можно продолжить
ранее спроектированные locality/profiling и acceleration линии как отдельные
подкампании с собственной provenance chain.

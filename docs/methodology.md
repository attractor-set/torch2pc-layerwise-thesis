# Методология

[English version](methodology_EN.md)

## Дизайн

Исследование является протокольно-ориентированным сравнением BP и вариантов
`predictive` `coding` в Torch2PC. Планы, [выполнение](glossary.md#term-execution), [доказательные материалы](glossary.md#term-evidence),
анализ и решения о допуске разделяются по коммитам и тегам. Отрицательные и
смешанные результаты сохраняются без изменения `frozen` `criteria`.

## Завершённые стадии

1. `pilot` и инфраструктурная проверка;
2. `Stage` 1 — исходный Torch2PC;
3. `Stage` 2 — `patched` Torch2PC при проверенной эквивалентности;
4. `Stage` 3A — послойные градиенты и представления;
5. `Stage` 3B B0 — каноническое ROCm/float32 [профилирование](glossary.md#term-profiling);
6. `SI-MA0` — `mechanism` `attribution` с сохранённым отрицательным `cost` `gate`;
7. `SI-MA1` — `matched` A/B/C `observer` `calibration` и итоговый `pass`;
8. теоретическая фиксация `PC-TREF`/`PC-CATM` перед B1/B2.

## Данные и независимая единица

Используются MNIST и FashionMNIST в зарегистрированных стадиях. Независимая
статистическая единица — независимо обученная модель, заданная `model_seed`.
`Batches`, слои, шаги, изображения и `timing` `blocks` являются вложенными
наблюдениями, а не дополнительными независимыми моделями.

`Validation` `split` используется для выбора, калибровки и `confirmatory` `analysis` в
рамках `frozen` `contracts`. `Test` `split` остаётся закрытым до итоговой фиксации
реализации, признаков, порогов и статистического плана.

## Контролируемая среда

GPU/ROCm выполнение проводится в каноническом Docker `image`. `Host` используется
для статических, Git- и документационных проверок. Каждая публикационная
кампания фиксирует `source` `commit`, `image` `revision`, Torch2PC `revision`,
конфигурацию, `checkpoint` `hashes` и `SHA256SUMS`.

## Измерения

- качество и сходимость;
- градиентная геометрия и послойная глубина;
- CKA, RSA и `cross-layer` `representation` `metrics`;
- `device` `time`, `wall` `time`, `memory` и `saved` `tensors`;
- канонические коррекционные каналы, `NCZ`, `ECZ`, `TNZ` и перенос;
- численная эквивалентность `candidate`/`reference`;
- `safety` `outcomes` и [regret решения](glossary.md#term-decision-regret);
- [вектор стоимости](glossary.md#term-cost-vector).

Все нормы `PC-CATM` задаются измерительным контрактом: пространство, норма,
масштаб, `dtype`, устройство, `epsilon`, `threshold`, слой/шаг и правило агрегации.
Пороговая близость не объявляется `quotient` без явной `partition` `map`.

## Разделение стоимости

Отдельно учитываются:

1. [стоимость диагностического механизма](glossary.md#term-diagnostic-mechanism-cost);
2. [стоимость наблюдателя](glossary.md#term-observer-cost);
3. [стоимость управляющего контура](glossary.md#term-control-plane-cost);
4. `fallback` и `end-to-end` `cost`.

`SI-MA1` относится к `observer` `boundary`. Его отрицательный `calibrated` `residual`
интерпретируется как `over-closure`, а не как отрицательная физическая стоимость
или будущая экономия.

## Метод B1/B2

Каждый `candidate` получает отдельную предварительную регистрацию до реализации.
Контракт фиксирует `reference` `path`, `state`/`belief`/`RNG` `restoration`, `scope`,
численные `endpoints` и `tolerances`, `independent` `unit`, `replacement` `policy`,
`safety`/`regret`, `cost` `vector`, `observer`/`control` `separation`, `fallback` и `stop` `rules`.

Последовательность:

1. `deterministic` и `unit` `controls`;
2. CPU `structural` `check`;
3. `controlled` ROCm `smoke`;
4. `candidate-specific` `numerical-equivalence` `gate`;
5. отдельное [решение о допуске](glossary.md#term-decision-gate) к `confirmatory` `profiling`;
6. `matched` `confirmatory` `execution`;
7. `aggregation` по `model_seed` без `post-hoc` исключений.

## Статистика

`Primary` `estimands`, направление теста, `bootstrap` `seed`, число повторов,
`multiplicity` `policy` и `threshold` фиксируются до `confirmatory` `execution`. Вложенные
измерения агрегируются до уровня `model_seed`. `Descriptive` `analyses` не
переименовываются в `confirmatory` `evidence` задним числом.

## Ограничения

Выводы ограничены зарегистрированными `datasets`, `lenet_classic`, Torch2PC
`revision`, `checkpoints`, float32/ROCm средой и семейством диагностик. B1/B2,
`active` `QWake-PC` и переносимость требуют собственных доказательных пакетов.

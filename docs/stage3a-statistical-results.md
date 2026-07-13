# Stage 3A: статистические результаты послойной диагностики

[English version](stage3a-statistical-results_EN.md)

## Область исследования

Stage 3A является подтверждающей диагностической подкампанией, выполненной в
закреплённой Ubuntu/ROCm-среде для одной экспериментальной области:

- dataset: FashionMNIST;
- architecture: `lenet_classic`;
- методы: BP, `Exact`, `FixedPred`, `Strict`;
- model seeds: 0–9;
- доступ к данным: validation-only diagnostic probes;
- статистическая единица: независимо обученная модель, то есть model seed.

Слои, batches, параметры и samples рассматриваются как повторные наблюдения
внутри seed. Они не увеличивают число независимых репликаций. Stage 3A не
использует test loader и не изменяет завершённые Stage 1/2 execution или
publication states.

Замороженный план анализа находится в
[`experiments/planned/STAGE3A-STATISTICAL-ANALYSIS.md`](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/stage3a-statistical-publication-v1/experiments/planned/STAGE3A-STATISTICAL-ANALYSIS.md).

## Входные данные и опубликованные результаты

| Артефакт | Размер |
|---|---:|
| Gradient observations | 2250 |
| Corresponding CKA/RSA observations | 150 |
| Cross-layer CKA observations | 750 |
| Seed-level gradient rows | 600 |
| Seed-level representation rows | 300 |
| Gradient statistical comparisons | 40 |
| Representation statistical comparisons | 20 |
| Exact numerical control rows | 30 |
| Depth seed-level rows | 180 |
| Depth statistical rows | 24 |
| Publication figures | 8 PDF |

Во всех зарегистрированных статистических сравнениях `n=10` и
`n_missing=0`.

## Статистический протокол

Для каждого model seed сначала формировались seed-level агрегаты. Затем
выполнялись парные сравнения относительно заранее заданных BP targets:

- cosine, norm ratio и sign agreement: target `1`;
- relative L2: target `0`;
- CKA и RSA Spearman: target `1`;
- depth Spearman: target отсутствия монотонного тренда `0`.

Использованы точные двусторонние sign-flip tests, Holm-коррекция внутри
зарегистрированных семейств, интервалы для среднего парного различия,
`Cohen dz` и rank-biserial correlation. Linear depth slopes сохранены как
описательные оценки; confirmatory inference для depth выполнялась по
seed-level Spearman coefficients.

## Exact numerical control

Все 30 строк основного Exact control прошли зарегистрированный tolerance
`1e-12`. Максимальная наблюдаемая absolute error составила
`1.354472090042691e-14`.

Depth control также сохранил практически нулевой тренд Exact:

- максимальный диапазон значений: `1.354472090042691e-14`;
- максимальный absolute slope: `1.1546319456101628e-15`.

Эти проверки подтверждают согласованность извлечения, агрегации и
сопоставления данных в закреплённой области. Они не являются универсальным
доказательством алгоритмической эквивалентности Torch2PC и BP.

## Градиенты FixedPred

На слоях 0, 1, 3 и 4 все четыре зарегистрированные метрики отличаются от BP
targets после Holm (`p_holm=0.0390625`). На выходном слое 5 значения совпадают
с targets в пределах численной точности и `p_holm=1`.

| Layer | Cosine | Norm ratio | Relative L2 | Sign agreement |
|---:|---:|---:|---:|---:|
| 0 | 0.994574 | 0.000881 | 0.999123 | 0.956667 |
| 1 | 0.999932 | 0.008326 | 0.991675 | 0.996358 |
| 3 | 1.000000 | 0.225160 | 0.774840 | 0.999793 |
| 4 | 1.000000 | 0.612580 | 0.387420 | 0.999848 |
| 5 | 1.000000 | 1.000000 | 0.000000 | 1.000000 |

В исследованной конфигурации `FixedPred` почти сохраняет направление
градиента, но сильно подавляет его норму в ранних слоях. Масштаб постепенно
приближается к BP к выходу, а layer 5 совпадает с BP targets.

## Градиенты Strict

Все 20 layer/metric comparisons для `Strict` отличаются от BP targets после
Holm (`p_holm=0.0390625`). В скрытых слоях наблюдаются одновременно
расхождения направления и масштаба:

- cosine: приблизительно `0.843–0.927`;
- sign agreement: приблизительно `0.822–0.868`;
- norm ratio возрастает от `0.000584` на layer 0 до `0.311747` на layer 4;
- relative L2 уменьшается от `0.999471` до `0.720317` на скрытых слоях.

Выходной layer 5 близок к BP, но не идентичен ему:

- cosine: `0.9999987`;
- norm ratio: `0.998449`;
- relative L2: `0.002240`;
- sign agreement: `0.999482`.

В этой области `Strict` создаёт не только depth-dependent scaling, но и
заметное direction mismatch в скрытых слоях.

## Нейронные представления

Все 20 CKA/RSA comparisons отличаются от BP target `1` после Holm
(`p_holm=0.01953125`). При этом `FixedPred` систематически ближе к BP, чем
`Strict`:

| Method | CKA range | RSA range |
|---|---:|---:|
| FixedPred | 0.988599–0.993861 | 0.983237–0.993475 |
| Strict | 0.960907–0.978650 | 0.940177–0.971826 |

Статистическое отличие от идеального target не означает автоматически
крупного практического эффекта. Для `FixedPred` абсолютные отклонения CKA/RSA
остаются малы в исследованной конфигурации.

## Depth analysis

Confirmatory depth inference использует Spearman coefficient, вычисленный
отдельно для каждого seed по ordinal layer depth.

| Domain | Method | Metric | Mean rho | Holm p |
|---|---|---|---:|---:|
| gradient | FixedPred | cosine | 1.00 | 0.0078125 |
| gradient | FixedPred | norm ratio | 1.00 | 0.0078125 |
| gradient | FixedPred | relative L2 | -1.00 | 0.0078125 |
| gradient | FixedPred | sign agreement | 0.97 | 0.0078125 |
| gradient | Strict | cosine | 0.54 | 0.0078125 |
| gradient | Strict | norm ratio | 1.00 | 0.0078125 |
| gradient | Strict | relative L2 | -1.00 | 0.0078125 |
| gradient | Strict | sign agreement | 0.59 | 0.0078125 |
| representation | FixedPred | CKA | -0.01 | 1.0000000 |
| representation | FixedPred | RSA | 0.47 | 0.0351563 |
| representation | Strict | CKA | -0.19 | 0.3027344 |
| representation | Strict | RSA | 0.51 | 0.0312500 |

Gradient norm ratio возрастает с глубиной, а relative L2 уменьшается для обоих
predictive-coding режимов. CKA не показывает надёжного monotonic depth trend.
RSA показывает умеренный положительный trend для `FixedPred` и `Strict`.

## Cross-layer CKA

Cross-layer CKA сохранён как описательный evidence-набор из 750 наблюдений.
Для candidate methods матрицы имеют максимальные средние значения на
соответствующих слоях:

| Method | Mean matched-layer CKA | Mean off-diagonal CKA |
|---|---:|---:|
| FixedPred | 0.991851 | 0.857415 |
| Strict | 0.972458 | 0.848253 |

Эти матрицы визуализируют структуру сходства между слоями, но не образуют
отдельное зарегистрированное confirmatory inferential family. Поэтому
cross-layer результаты интерпретируются описательно.

## Ограничения effect sizes и p-values

- Exact sign-flip p-values дискретны при `n=10`; минимальное двустороннее
  значение равно `0.001953125`.
- Очень большие абсолютные `Cohen dz` для norm ratio и relative L2 возникают
  при почти нулевой межseed вариативности. Они отражают стабильное отклонение
  от target, но не должны читаться как универсальная мера практической
  значимости.
- Значимость относительно идеальных targets `1/0` не заменяет оценку качества
  обучения, runtime, памяти или downstream utility.
- Слои и batches не являются независимыми репликациями.

## Угрозы валидности

1. Исследован один dataset и одна architecture.
2. Использованы 10 независимо обученных seeds.
3. Анализ ограничен validation-only diagnostic probes.
4. Результаты относятся к закреплённым Torch2PC commits, dtype, конфигурациям и
   Ubuntu/ROCm-среде.
5. Представления сравниваются между независимо обученными checkpoints, поэтому
   вывод ограничен используемыми CKA/RSA процедурами.
6. Новые datasets, architectures, hyperparameters, hardware или реализации
   требуют отдельной preregistered campaign.

## Ограниченные выводы

В исследованной конфигурации:

- `Exact` проходит зарегистрированные numerical controls относительно BP;
- `FixedPred` преимущественно сохраняет направление градиента, одновременно
  создавая сильное раннеслойное attenuation масштаба;
- `Strict` в скрытых слоях расходится с BP и по направлению, и по масштабу;
- `FixedPred` representations ближе к BP, чем `Strict`, хотя обе группы
  статистически отличаются от идеального BP target;
- gradient alignment имеет выраженную depth-dependent структуру;
- CKA не демонстрирует надёжного monotonic depth trend, тогда как RSA имеет
  умеренный положительный trend.

Эти выводы не обобщаются за пределы FashionMNIST, `lenet_classic`, seeds 0–9,
закреплённой реализации и validation-only Stage 3A protocol.

## Артефакты и provenance

Статистика:

- [каталог statistics](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/stage3a-statistical-publication-v1/results/stage3/layerwise/confirmatory/statistics);
- [analysis metadata](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/stage3a-statistical-publication-v1/results/stage3/layerwise/confirmatory/statistics/analysis_metadata.json);
- [depth analysis metadata](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/stage3a-statistical-publication-v1/results/stage3/layerwise/confirmatory/statistics/depth_analysis_metadata.json);
- [statistics SHA256SUMS](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/stage3a-statistical-publication-v1/results/stage3/layerwise/confirmatory/statistics/SHA256SUMS).

Figures:

- [каталог figures](https://github.com/attractor-set/torch2pc-layerwise-thesis/tree/stage3a-statistical-publication-v1/results/stage3/layerwise/confirmatory/figures);
- [figure metadata](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/stage3a-statistical-publication-v1/results/stage3/layerwise/confirmatory/figures/figure_metadata.json);
- [figures SHA256SUMS](https://github.com/attractor-set/torch2pc-layerwise-thesis/blob/stage3a-statistical-publication-v1/results/stage3/layerwise/confirmatory/figures/SHA256SUMS).

Проверка committed evidence выполняется без перегенерации:

```bash
(
  cd results/stage3/layerwise/confirmatory/statistics
  sha256sum -c SHA256SUMS
)

(
  cd results/stage3/layerwise/confirmatory/figures
  sha256sum -c SHA256SUMS
)
```

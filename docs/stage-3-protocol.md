# Протокол Stage 3: локальность, аппроксимация и масштабирование

[English version](stage-3-protocol_EN.md)

Статус: **design-ready; исполнение заблокировано до реализации кандидатов,
численных gates и отдельной заморозки Stage 3**.

## 1. Назначение

Stage 3 является новой самостоятельной кампанией. Он не изменяет и не
переоткрывает Stage 1 или Stage 2. Его задача — исследовать связь между:

- математической послойной локальностью predictive coding;
- размером и связностью фактически исполняемого autograd graph;
- числом VJP, синхронизаций и сохраняемых тензоров;
- временем, памятью и масштабированием по глубине;
- точными и приближёнными вариантами вычисления credit signal;
- качеством, устойчивостью и gradient alignment.

Stage 3 разделяет два типа изменений:

1. **implementation-preserving:** меняется организация точных вычислений, а
   формулы update rule сохраняются;
2. **algorithm-changing approximation:** изменяется stopping rule, частота
   обновления линеаризации или feedback operator.

Результаты этих треков анализируются отдельно.

## 2. Неизменяемый baseline

| Роль | Идентификатор |
|---|---|
| Stage 2 execution source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Stage 2 publication state | `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| Stage 2 Torch2PC | `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |
| Наблюдаемый runtime order | `BP ≈ Exact < FixedPred << Strict` |

Execution source и publication state сохраняются как разные provenance points.
Tags Stage 2 не перемещаются. Stage 1/2 не перезапускаются для создания новой
Stage 3 кампании.

## 3. Исследовательские вопросы

### RQ6. Профиль локальности

Какие зависимости, graph span, VJP calls, synchronization points и saved tensor
bytes фактически возникают для обновления каждого слоя FixedPred и Strict?

### RQ7. Локальность исполнения и throughput

Как меняются runtime и память при переходе между независимыми layer-local graphs
и composite VJP, когда математический update rule сохраняется?

### RQ8. Адаптивный вычислительный бюджет

Как adaptive stopping влияет на число inference iterations, gradient alignment,
runtime, память и validation quality?

### RQ9. Частота обновления линеаризации

Как periodic или state-triggered VJP refresh изменяет trade-off между Strict и
FixedPred?

### RQ10. Приближённый feedback

Может ли отдельный локальный feedback operator уменьшить вычислительную
стоимость при заранее заданной non-inferiority границе и публикуемом изменении
gradient alignment?

RQ10 является условным расширением. Он начинается только после завершения
основной линии Stage 3 и при наличии временного резерва.

## 4. Таксономия локальности

Один суммарный locality score не используется. Публикуется вектор измерений.

### 4.1. Algorithmic locality

Для update слоя фиксируется набор математических входов: состояние слоя,
состояния соседей, prediction errors и параметры локального модуля.

### 4.2. Dependency radius

Для слоя `l` dependency radius определяется как максимальное расстояние до слоя,
данные которого использует событие. Для posлойного PC основной structural gate
равен `radius <= 1`.

### 4.3. Graph locality

Записываются номера модулей, входящих в исполняемый autograd graph, и его span.
Composite execution может иметь больший graph span при сохранённой локальной
математике.

### 4.4. Execution locality

Фиксируется возможность отдельного построения, исполнения и освобождения graph
для слоя, а также доступ к общему scheduler и global loss graph.

### 4.5. Feedback locality

Различаются exact Jacobian-transpose product, reused exact pullback и отдельный
approximate feedback operator.

### 4.6. Orchestration locality

Фиксируются последовательные reverse updates, synchronous/Jacobi updates,
число barriers и synchronization points.

## 5. Кандидаты

### B0. `stage2_baseline`

Доступный контроль на Torch2PC
`b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

### B1. `isolated_layer_vjp`

Каждый слой использует detached leaf inputs и собственный local graph.

- track: implementation-preserving;
- методы: FixedPred, Strict;
- обязательны CPU/GPU equivalence gates;
- ожидаемый эффект: больше execution locality, возможный рост engine overhead.

### B2. `composite_vjp`

Локальные VJP группируются в минимальное число autograd invocations.

- track: implementation-preserving;
- методы: FixedPred, Strict;
- обязательны те же equivalence gates;
- ожидаемый эффект: меньше Python/autograd overhead, больший graph span.

### C1. `adaptive_stopping`

Inference завершается по residual criterion после `minimum_steps` и до
`maximum_steps`.

- track: approximation;
- методы: FixedPred, Strict;
- критерий и tolerance выбираются только по validation pilot;
- фактическое число iterations сохраняется для каждого batch.

### C2. `periodic_vjp_refresh`

Strict пересчитывает pullback через заданный интервал или по state residual.

- track: approximation;
- метод: Strict;
- начальная сетка interval: `1, 2, 5, 20`;
- `interval=1` является Strict-like control;
- большое значение приближается к fixed-linearization regime.

### C3. `fixed_random_feedback`

Отдельный feedback operator заменяет exact VJP.

- track: approximation;
- начальный статус: deferred;
- метод: Strict;
- отдельная exploratory provenance chain;
- отсутствие требований equivalence с Stage 2.

## 6. Фазы

### 6.1. Stage 3A — baseline audit и profiling

Сначала профилируется B0 без test и без изменения алгоритма.

Размечаемые регионы:

- `initial_forward`;
- `state_inference`;
- `local_state_vjp`;
- `parameter_vjp`;
- `optimizer_step`.

Сохраняемые показатели:

- CPU self time;
- device/kernel time;
- число VJP/autograd invocations;
- число synchronization points;
- saved tensor bytes;
- peak allocated и reserved memory;
- dependency radius;
- graph span;
- фактическое число inference iterations.

После реализации B1/B2 те же microbenchmarks повторяются для кандидатов.

### 6.2. Stage 3B — точные implementation-preserving кандидаты

Порядок:

1. B1 isolated layer VJP;
2. CPU float64 equivalence;
3. GPU float32 equivalence;
4. B2 composite VJP;
5. те же gates;
6. back-to-back randomized profiling B0/B1/B2;
7. выбор точного кандидата для pilot.

B1 и B2 не объединяются до завершения attribution анализа.

### 6.3. Stage 3C — аппроксимации

Порядок:

1. C1 adaptive stopping;
2. C2 periodic refresh;
3. C3 feedback operator только после go/no-go.

Каждая аппроксимация получает отдельный candidate ID и не наследует
implementation-equivalence claim B1/B2.

### 6.4. Stage 3D — scaling

Добавлено контролируемое семейство:

- depths: `4, 8, 16, 32`;
- widths: `64, 256`;
- batch sizes: `64, 256`;
- methods: FixedPred, Strict;
- profiling seeds: `70, 71, 72`.

Имена моделей имеют форму `mlp_d<depth>_w<width>`.

## 7. План profiling

Декларативная матрица содержит:

```text
2 methods
x 3 exact candidates (B0/B1/B2)
x 4 depths
x 2 widths
x 2 batch sizes
x 3 seeds
= 288 profiling cells
```

Каждая ячейка является коротким benchmark, а не полным обучением:

- 20 warmup steps;
- 50 measured steps;
- 5 repetitions;
- отдельная синхронизация перед и после измеряемого региона;
- randomized back-to-back order внутри matched block.

## 8. Validation-only pilot

Pilot не создаёт test loader.

Screening разворачивает параметры аппроксимаций до их заморозки:

```text
B0/B1/B2 defaults:
  3 candidates x 2 methods x 3 seeds = 18 cells
C1 adaptive stopping:
  3 tolerances x 2 methods x 3 seeds = 18 cells
C2 periodic refresh:
  4 intervals x Strict x 3 seeds = 12 cells
Total = 48 validation-only terminal cells
```

Для C1 используются tolerance `1e-2`, `5e-3`, `1e-3`; maximum steps равен 10
для FixedPred и 20 для Strict. Для C2 используются intervals `1, 2, 5, 20`.
Каждая ячейка plan содержит `variant_id` и полный набор параметров, поэтому
после выполнения можно однозначно воспроизвести выбор.

Pilot используется для:

- проверки стабильности;
- настройки tolerance adaptive stopping;
- выбора refresh interval;
- выбора одного точного и одного approximate candidate;
- оценки paired validation variation;
- фиксации practical non-inferiority margin.

MNIST и test не участвуют в выборе кандидатов.

## 9. Final template

До freeze final template имеет:

```yaml
evaluation:
  use_test: false
protocol:
  status: blocked_until_stage3_freeze
```

После pilot и freeze предполагается:

```text
2 datasets
x применимые candidate-method pairs
x 10 seeds
= максимум 80 final cells
```

Два кандидата:

1. один implementation-preserving candidate;
2. один approximation candidate.

Если выбран `periodic_vjp_refresh`, он применяется только к Strict, поэтому
матрица содержит 60 ячеек: 40 для точного кандидата и 20 для approximation.
Если approximation candidate не проходит pilot gates, final сокращается до
40 ячеек точного кандидата. Решение фиксируется до любого Stage 3 test access.

## 10. Gates

### 10.1. Structural locality gate

Для mathematically local events требуется `dependency_radius <= 1`. Graph span
публикуется отдельно и не смешивается с dependency radius.

### 10.2. Implementation equivalence gate

Для B1/B2 сравниваются:

- beliefs;
- prediction errors;
- state updates;
- parameter gradients;
- параметры после одного optimizer step.

Метрики:

- max absolute error;
- relative L2;
- cosine similarity;
- non-finite count.

Пороги стартуют с области Stage 2:

| Device | dtype | min cosine | max relative L2 |
|---|---|---:|---:|
| CPU | float64 | 0.99999 | `1e-7` |
| GPU | float32 | 0.999 | `1e-3` |

Изменение порогов требует ADR до pilot.

### 10.3. Approximation gate

Для C1/C2 equivalence не заявляется. Сравниваются:

- per-layer gradient cosine;
- relative L2;
- sign agreement;
- state/energy residual;
- iteration/VJP reduction;
- validation macro F1;
- seed variance;
- non-finite events.

Non-inferiority margin определяется из Stage 2 seed variability и Stage 3 pilot,
а не задаётся после просмотра Stage 3 test.

### 10.4. Performance gate

Engineering go/no-go:

- FixedPred: не менее 15% устойчивого speedup;
- Strict: не менее 20% устойчивого speedup;
- regression B0/BP/Exact timing не более 3%;
- рост peak memory не более 15% без отдельного обоснования.

Эти пороги определяют продолжение инженерной разработки и сами по себе не
создают статистический вывод о превосходстве.

## 11. Feasibility stop rules

Полная реализация кандидата прекращается, если:

- optimizable region занимает менее 20% runtime;
- Amdahl upper bound меньше 15% для FixedPred или 20% для Strict;
- выигрыш возникает только за счёт изменения batch, dtype или workload;
- новый candidate создаёт non-finite значения;
- exact candidate не проходит численные gates;
- approximate candidate не проходит validation non-inferiority gate.

Отрицательный результат сохраняется в registry и отчёте.

## 12. Порядок доступа к test

- profiling: test отсутствует;
- Stage 3 pilot: test отсутствует;
- Stage 3 final template: test выключен;
- test включается отдельным commit только после `stage3-pilot-freeze-v1`;
- после открытия test изменения candidate parameters маркируются exploratory.

Stage 1/2 test результаты могут использоваться только как уже опубликованные
historical observations. Они не используются для настройки Stage 3 кандидатов.

## 13. Provenance chain

Планируемые точки:

1. Stage 3 design commit;
2. tag `stage3-design-v1`;
3. отдельные Torch2PC commits для B1/B2/C1/C2;
4. Stage 3 profiling environment lock;
5. CPU/GPU candidate gates;
6. validation-only pilot registry snapshot;
7. Stage 3 pilot freeze;
8. tag `stage3-pilot-freeze-v1`;
9. Stage 3 execution commit и tag `stage3-execution-v1`;
10. Stage 3 results/publication state и tag `stage3-results-v1`.

Execution и publication state остаются разными commits.

## 14. Артефакты

```text
results/stage-3/
├── profiling/
│   ├── traces/
│   ├── summaries/
│   ├── tables/
│   └── figures/
├── pilot/
│   ├── summaries/
│   └── tables/
├── final/
│   ├── summaries/
│   ├── tables/
│   └── figures/
└── README.md
```

Минимальный locality event следует схеме
`src/torch2pc_thesis/locality.py` и содержит candidate, method, phase, step,
layer, touched layers, graph modules, VJP calls, synchronization points, saved
tensor bytes и timings. `src/torch2pc_thesis/profiling.py` закрепляет имена
измеряемых регионов, timing summary и Amdahl feasibility calculation.

## 15. Двенадцатимесячный план

| Период | Результат |
|---|---|
| Месяцы 1–2 | literature update, RQ/ADR, design freeze, profiling executor |
| Месяцы 3–4 | B0 audit, locality traces, scaling family, baseline report |
| Месяцы 5–6 | B1/B2 implementation и equivalence gates |
| Месяц 7 | C1/C2 implementation и validation-only pilot |
| Месяц 8 | candidate freeze и core final execution |
| Месяц 9 | conditional C3 go/no-go |
| Месяц 10 | robustness, representations, scaling analysis |
| Месяц 11 | dissertation chapter, article, replication bundle |
| Месяц 12 | clean-room reproduction, review corrections, reserve |

## 16. Текущее определение readiness

Текущее состояние называется **ready for Stage 3 implementation**, если:

- protocol, ADR и design YAML существуют;
- provenance baseline закреплён полными hashes;
- Stage 1/2 объявлены immutable;
- locality trace schema реализована и протестирована;
- scaling model family реализована и протестирована;
- deterministic profiling/pilot plan формируется;
- Stage 3 stages не входят в исполняемый `TRAINING_STAGES`;
- final template сохраняет test выключенным.

Это состояние не означает готовность к pilot или final execution. Переход к ним
требует реализации кандидатов, окружения, numerical gates и freeze artifacts.

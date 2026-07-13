# Stage 3B: preregistration профилирования и локальности

[English version](STAGE3B-PROFILING-LOCALITY_EN.md)

Статус: **preregistered design; execution blocked**.

Дата фиксации: 2026-07-13.

## 1. Назначение и граница этапа

Stage 3B создаёт измерительную основу для последующих утверждений о
локальности, стоимости и возможном ускорении predictive coding в Torch2PC.
Этап измеряет существующую реализацию и точные кандидаты до выбора
algorithm-changing approximation.

Stage 3B не переоткрывает Stage 1, Stage 2 или опубликованную Stage 3A
диагностику. Test dataset остаётся недоступным. Результаты profiling не
трактуются как доказательство универсального превосходства какого-либо
метода.

## 2. Уточнение названия

Ранний Stage 3 design revision 2 использовал название `Stage 3A` для
profiling. После публикации отдельной диагностической кампании под tag
`stage3a-results-v1` следующий перспективный этап называется
`Stage 3B profiling/locality`.

Это уточнение будущей номенклатуры:

- опубликованные commits, paths, manifests и tags Stage 3A не изменяются;
- исторические документы сохраняют исходную формулировку;
- новые implementation, execution и publication artifacts используют
  префикс `stage3b`.

## 3. Неизменяемая provenance-база

| Роль | Идентификатор |
|---|---|
| Project baseline | `b05e97c9917f06b1b46d84a259f2aa7de9f24379` |
| Stage 3A publication tag | `stage3a-results-v1` |
| Stage 2 execution source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Stage 2 publication state | `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| Patched Torch2PC | `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |

Stage 2 execution/publication tags и Stage 3A evidence tags не перемещаются.
Новая кампания получает отдельную commit и tag chain.

## 4. Исследовательские вопросы

### RQ-P1. Attribution стоимости

Какая доля CPU/device time, VJP/autograd calls, synchronization points,
saved tensor bytes и peak memory приходится на отдельные регионы
`FixedPred` и `Strict`?

### RQ-P2. Многомерная локальность

Как соотносятся algorithmic dependency radius, graph span, independent
lifetime, feedback operator и orchestration barriers в реальном
исполнении Torch2PC?

### RQ-P3. Масштабирование

Как depth, width и batch size изменяют runtime, memory, VJP count и
locality profile при matched конфигурациях?

### RQ-P4. Точные кандидаты

Изменяют ли B1 `isolated_layer_vjp` и B2 `composite_vjp` runtime или
memory после прохождения full-trajectory equivalence gates?

### RQ-P5. Exact-shortcut control

Сохраняет ли A0 `fixedpred_finite_step_control` endpoint gradients и один
optimizer step в закреплённой области, и какую верхнюю границу возможного
сокращения стоимости он показывает?

## 5. Кандидаты и последовательность

| ID | Кандидат | Track | Разрешение на profiling |
|---|---|---|---|
| B0 | `stage2_baseline` | baseline | после non-perturbation gate |
| A0 | `fixedpred_finite_step_control` | exact shortcut | после endpoint gate |
| B1 | `isolated_layer_vjp` | implementation-preserving | после CPU/GPU full-trajectory gate |
| B2 | `composite_vjp` | implementation-preserving | после CPU/GPU full-trajectory gate |

Порядок выполнения:

1. реализовать non-perturbing profiler;
2. проверить инструментированный B0 относительно неинструментированного B0;
3. выполнить B0/A0 smoke и attribution audit;
4. реализовать B1 отдельным commit и пройти exact gates;
5. реализовать B2 отдельным commit и пройти exact gates;
6. только затем выполнить полную randomized matched profiling matrix.

B1 и B2 не объединяются до отдельного attribution analysis.

## 6. Матрица profiling

Контролируемое MLP-семейство:

- depth: `4, 8, 16, 32`;
- width: `64, 256`;
- batch size: `64, 256`;
- model seeds: `70, 71, 72`.

Матрица:

```text
B0/B1/B2:
3 candidates × 2 methods × 4 depths × 2 widths × 2 batches × 3 seeds
= 288 matched cells

A0:
1 candidate × FixedPred × 4 depths × 2 widths × 2 batches × 3 seeds
= 48 matched cells

Total = 336 short matched cells
```

A0 применяется только к `FixedPred`. B0/B1/B2 профилируются для
`FixedPred` и `Strict`.

## 7. Единицы наблюдения и агрегация

Независимая исследовательская единица — `model_seed`.

- repetition является технической репликацией внутри cell;
- measured steps являются повторными измерениями внутри repetition;
- regions и layers являются вложенными наблюдениями;
- они не увеличивают независимое `n`.

Для каждой cell сначала рассчитывается median по measured steps внутри
repetition, затем median по пяти repetitions. Сравнения кандидатов
выполняются попарно внутри одинаковых `method × depth × width × batch ×
model_seed`.

Поскольку profiling использует три model seeds, основной анализ является
описательным и инженерным. Дискретные p-values при `n=3` не используются
для научных claims о превосходстве.

## 8. Измерительный протокол

Каждая cell выполняет:

- `20` warm-up steps;
- `50` measured steps;
- `5` repetitions;
- явную device synchronization на определённых boundaries;
- hash-counterbalanced candidate order;
- один и тот же resolved config для matched comparisons.

Основные регионы:

- `initial_forward`;
- `state_inference`;
- `local_state_vjp`;
- `parameter_vjp`;
- `optimizer_step`.

Обязательные метрики:

- host wall time;
- device time;
- VJP/autograd call count;
- explicit synchronization count;
- saved tensor bytes;
- peak allocated/reserved device memory;
- actual inference steps;
- graph modules и graph span;
- dependency radius;
- graph lifetime/freedom point;
- feedback operator type;
- non-finite и profiler-integrity events.

Runtime comparisons используют одинаковые synchronization rules. Стоимость
самой instrumentation публикуется отдельно и не вычитается скрыто.

## 9. Таксономия локальности

Публикуются отдельные измерения:

1. **algorithmic locality** — математические входы update;
2. **dependency radius** — максимальное расстояние до используемого слоя;
3. **graph locality** — модули и span одного autograd graph;
4. **execution locality** — возможность независимого build/execute/free;
5. **feedback locality** — exact, reused exact или approximate operator;
6. **orchestration locality** — порядок, barriers и synchronization points.

Единый locality score не рассчитывается. Structural gate
`dependency_radius <= 1` применяется только к событиям, заранее
объявленным mathematically layer-local.

## 10. Численные и измерительные gates

### 10.1. Non-perturbation gate profiler

Инструментированный и неинструментированный B0 должны совпадать по:

- beliefs и prediction errors;
- state updates;
- parameter gradients;
- одному optimizer step;
- числу фактически выполненных inference steps.

Пороговые значения:

| Device | dtype | min cosine | max relative L2 |
|---|---|---:|---:|
| CPU | float64 | `0.99999` | `1e-7` |
| GPU | float32 | `0.999` | `1e-3` |

### 10.2. B1/B2 full-trajectory gate

B1 и B2 допускаются к matched profiling только после совпадения полной
траектории в пределах тех же CPU/GPU thresholds.

### 10.3. A0 endpoint gate

A0 допускается после совпадения parameter gradients и одного optimizer
step. Эквивалентность промежуточной beliefs trajectory не заявляется.

### 10.4. Completeness gate

Cell считается измерительно завершённой, если:

- сохранены все пять repetitions;
- каждый repetition содержит 50 measured steps;
- обязательные regions и counters присутствуют;
- отсутствуют новые non-finite events;
- resolved config, environment lock и source identifiers сохранены;
- output manifest и SHA-256 проходят проверку.

Неполная cell сохраняется как failed/incomplete и не заменяется молча.

## 11. Engineering continuation rules

Следующие thresholds используются только как правила продолжения
разработки, а не как claims о превосходстве:

- FixedPred speedup: не менее `15%`;
- Strict speedup: не менее `20%`;
- baseline regression: не более `3%`;
- memory growth: не более `15%` без отдельного ADR.

Также публикуются absolute times, paired deltas, VJP reduction, memory
change, instrumentation overhead и Amdahl upper bound.

## 12. Stop rules

Кандидат или profiling block останавливается при:

- провале numerical gate;
- изменении optimizer trajectory для implementation-preserving track;
- non-finite values;
- отсутствующих или несогласованных profiler events;
- недостаточном optimizable fraction;
- Amdahl upper bound ниже continuation threshold;
- baseline regression выше закреплённой границы;
- неконтролируемом росте памяти;
- нарушении test isolation или provenance chain.

Отрицательный результат и failed cells сохраняются в registry.

## 13. Test isolation

Stage 3B не создаёт test loader и не вычисляет test metrics.

Разрешены:

- synthetic scaling family для profiling;
- training/validation data там, где они необходимы для smoke или gate;
- numerical controls на закреплённых minibatches.

Test может быть открыт только отдельным commit после последующего
pilot freeze. Успех profiling не даёт такого разрешения автоматически.

## 14. Планируемые outputs

Публичный evidence root:

```text
results/stage3/profiling/
```

Минимальный набор:

- `profiling_cells.csv`;
- `profiling_repetitions.csv`;
- `locality_events.jsonl`;
- `profiling_summary.csv`;
- `analysis_metadata.json`;
- `environment-lock.json`;
- `SHA256SUMS`.

Metadata должна включать project commit, Torch2PC commit, resolved config
hashes, environment versions, device identifiers, timing backend,
synchronization policy, timestamps и SHA-256 inputs/outputs.

## 15. Commit и tag chain

Рекомендуемая последовательность:

1. `research: preregister Stage 3B profiling and locality`;
2. `feat: add non-perturbing Stage 3B profiler`;
3. `test: add Stage 3B profiler integrity gates`;
4. `research: lock Stage 3B profiling environment`;
5. `research: publish Stage 3B B0/A0 smoke evidence`;
6. отдельные implementation и gate commits B1/B2;
7. execution commit/tag;
8. evidence commit;
9. checksum commit;
10. publication documentation commit/tag.

Планируемые tags:

- `stage3b-profiling-prereg-v1`;
- `stage3b-profiling-execution-v1`;
- `stage3b-profiling-results-v1`.

Execution и publication states являются разными provenance points. История
не переписывается; force-push для опубликованных веток и tags не
используется.

## 16. Разрешение на начало реализации

После merge этой preregistration разрешена только реализация profiler и
его unit/integrity tests. Полная profiling matrix остаётся заблокированной
до выполнения non-perturbation, environment-lock и candidate-specific
gates.

# Протокол Stage 3: локальность, аппроксимация и predict-correct acceleration

[English version](stage-3-protocol_EN.md)

Статус: **design-ready revision 2; исполнение заблокировано до реализации
кандидатов, численных gates и отдельной заморозки Stage 3**.

## 1. Назначение

Stage 3 является новой самостоятельной кампанией и не переоткрывает Stage 1/2.
Он исследует связь между математической локальностью, реальной организацией
autograd, числом VJP, памятью, runtime, глубиной и контролируемыми
аппроксимациями.

Три типа изменений анализируются раздельно:

1. **implementation-preserving** — точные формулы и полная траектория update
   сохраняются;
2. **exact shortcut** — сохраняется теоретически ожидаемый endpoint, но не
   обязательно промежуточная траектория beliefs;
3. **algorithm-changing approximation** — stopping, stale linearization,
   predict-correct, preconditioning или approximate feedback.

## 2. Неизменяемый baseline

| Роль | Идентификатор |
|---|---|
| Stage 2 execution source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Stage 2 publication state | `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| Stage 2 Torch2PC | `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |
| Runtime order | `BP ≈ Exact < FixedPred << Strict` |

Execution source и publication state остаются разными provenance points. Tags
Stage 2 не перемещаются. Stage 1/2 не перезапускаются.

## 3. Исследовательские вопросы

### RQ6. Профиль локальности

Какие dependency radius, graph span, VJP calls, synchronization points и saved
tensor bytes возникают для послойных обновлений FixedPred и Strict?

### RQ7. Локальность исполнения и throughput

Как isolated layer-local graphs и composite VJP изменяют runtime и память при
сохранённой математике?

### RQ8. Адаптивный бюджет

Как adaptive stopping влияет на число inference steps, alignment, runtime,
память и validation quality?

### RQ9. Частота линеаризации

Как periodic/state-triggered VJP refresh изменяет trade-off между Strict и
FixedPred?

### RQ10. Приближённый feedback

Может ли локальный approximate feedback с редкой точной коррекцией уменьшить
стоимость при контролируемой потере alignment и качества?

### RQ11. Predict-correct acceleration

Может ли дешёвая локальная оценка beliefs или локального обратного масштаба,
после которой выполняются `1–5` точных PC correction sweeps, сократить VJP и
runtime без practically meaningful потери качества?

## 4. Таксономия локальности

Публикуется профиль, а не один locality score:

- **algorithmic locality:** математические входы update;
- **dependency radius:** максимальное расстояние до используемого слоя;
- **graph locality:** модули и span одного autograd graph;
- **execution locality:** возможность независимого build/execute/free;
- **feedback locality:** exact, reused exact или approximate operator;
- **orchestration locality:** порядок, barriers и synchronization points.

Для математически локальных событий structural gate равен
`dependency_radius <= 1`.

## 5. Кандидаты

### B0. `stage2_baseline`

Закреплённый patched Torch2PC Stage 2.

### A0. `fixedpred_finite_step_control`

FixedPred с `eta=1` и числом шагов, равным глубине сети.

- track: exact shortcut;
- метод: FixedPred;
- gate: endpoint gradients и один optimizer step;
- промежуточная trajectory equivalence не заявляется;
- роль: точный shortcut/control и верхняя граница достижимого ускорения.

### B1. `isolated_layer_vjp`

Detached leaf inputs и отдельный local graph на слой. Требуется
full-trajectory CPU/GPU equivalence.

### B2. `composite_vjp`

Группировка локальных VJP в минимальное число autograd invocations. Требуется
full-trajectory CPU/GPU equivalence.

### C1. `adaptive_stopping`

Residual-based остановка между `minimum_steps` и `maximum_steps`.

### C2. `periodic_vjp_refresh`

Strict обновляет pullback с interval `1, 2, 5, 20`; `1` — Strict-like control.

### C3. `fixed_random_feedback`

Чистый approximate feedback. Статус deferred.

### C3H. `hybrid_feedback_exact_refresh`

Дешёвый feedback между периодическими точными VJP и обязательной финальной
точной коррекцией. Статус deferred.

### C4. `predict_correct_initialization`

Дешёвый layer-local initializer:

```text
v0 = feedforward_state + EMA(local equilibrium correction)
v  = exact_pc_correct(v0, steps=1/2/3/5)
```

Основная спецификация revision 2 использует `layerwise_ema_residual`,
`ema_beta=0.9`, reset в начале эпохи и fallback на Strict при `NaN/Inf` или
росте residual.

### C5. `local_secant_preconditioner`

После двух точных warmup sweeps оценивается layer-scalar secant scale,
ограниченный диапазоном `[0.25, 4.0]`, затем выполняются `1/2/3/5` точных
correction sweeps. Fallback на Strict обязателен.

### C6. `layer_local_anderson`

Layer-local Anderson mixing с window `2/3`. Статус deferred из-за хранения
history и риска снижения locality.

## 6. Фазы

### 6.1. Stage 3A — profiling

Регионы:

- `initial_forward`;
- `state_inference`;
- `local_state_vjp`;
- `parameter_vjp`;
- `optimizer_step`.

Метрики: CPU/device time, VJP/autograd calls, synchronization points, saved
tensor bytes, peak memory, graph span, dependency radius и фактические steps.

Profiling включает B0, A0, B1 и B2. A0 применяется только к FixedPred.

### 6.2. Stage 3B — точные кандидаты

Порядок: B1 → gates → B2 → gates → A0 endpoint gate → randomized matched
profiling. B1/B2 не объединяются до attribution analysis.

### 6.3. Stage 3C — core approximations

Порядок: C1 adaptive stopping → C2 periodic refresh → validation-only core
pilot. Эти кандидаты получают non-inferiority, но не equivalence claim.

### 6.4. Stage 3C2 — predict-correct accelerator screening

После core pilot отдельно сравниваются B0 Strict, C4 и C5. C3H/C6 остаются
deferred. Этот этап не создаёт test loader и не может автоматически изменить
final template.

### 6.5. Stage 3D — scaling

Контролируемое семейство MLP:

- depth `4, 8, 16, 32`;
- width `64, 256`;
- batch size `64, 256`;
- seeds `70, 71, 72`.

## 7. Матрицы

### 7.1. Profiling

```text
B0/B1/B2: 3 candidates x 2 methods x 4 depths x 2 widths x 2 batches x 3 seeds = 288
A0:       1 candidate  x 1 method  x 4 depths x 2 widths x 2 batches x 3 seeds = 48
Total = 336 short matched cells
```

Каждая ячейка: 20 warmup, 50 measured steps, 5 repetitions, device sync и
hash-counterbalanced order.

### 7.2. Core validation-only pilot

```text
B0/B1/B2 defaults: 18
C1: 3 tolerances x 2 methods x 3 seeds = 18
C2: 4 intervals x Strict x 3 seeds = 12
Total = 48 cells
```

### 7.3. Predict-correct accelerator screening

```text
B0 Strict: 1 variant x 3 seeds = 3
C4: 4 correction budgets x 3 seeds = 12
C5: 4 correction budgets x 3 seeds = 12
Total = 27 validation-only cells
```

FashionMNIST/`lenet_classic` используется для выбора. MNIST и test не участвуют.

### 7.4. Final template

До freeze:

```yaml
evaluation:
  use_test: false
protocol:
  status: blocked_until_stage3_freeze
```

После freeze: до 80 cells для одного точного и одного approximation candidate.
Strict-only approximation даёт 60 cells. Если approximation не проходит gates,
остаётся 40-cell exact track.

## 8. Gates

### 8.1. Full-trajectory equivalence

B1/B2: beliefs, prediction errors, state updates, parameter gradients и один
optimizer step.

| Device | dtype | min cosine | max relative L2 |
|---|---|---:|---:|
| CPU | float64 | 0.99999 | `1e-7` |
| GPU | float32 | 0.999 | `1e-3` |

### 8.2. Endpoint equivalence

A0: parameter gradients и один optimizer step. Внутренние beliefs и порядок
распространения ошибок не обязаны совпадать.

### 8.3. Approximation/non-inferiority

C1–C6: per-layer cosine, relative L2, sign agreement, residual, VJP/step
reduction, validation macro F1, seed variance и non-finite events.

### 8.4. Predict-correct guard

C4/C5 продолжаются только если:

- есть хотя бы один exact correction sweep;
- среднее сокращение VJP не меньше 25%;
- fallback fraction не больше 10%;
- residual не растёт после correction;
- отсутствуют новые non-finite events;
- validation non-inferiority выполнена.

Fallback events публикуются и учитываются в runtime; они не удаляются как
«неудачные samples».

### 8.5. Performance

- FixedPred speedup: не менее 15%;
- Strict speedup: не менее 20%;
- baseline regression: не более 3%;
- memory growth: не более 15% без ADR.

Это engineering continuation rules, а не superiority claims.

## 9. Stop rules

Кандидат останавливается при малой optimizable fraction, недостаточном Amdahl
upper bound, провале exact gate, non-finite values, росте residual,
fallback >10% или провале validation non-inferiority. Отрицательный результат
сохраняется в registry.

## 10. Test access и provenance

Profiling, core pilot, accelerator screening и текущий final template сохраняют
test выключенным. Test включается отдельным commit после
`stage3-pilot-freeze-v1`.

Planned tags:

- `stage3-design-v1`;
- `stage3-pilot-freeze-v1`;
- `stage3-execution-v1`;
- `stage3-results-v1`.

Execution и publication states остаются разными commits.

## 11. Годовой график

| Период | Результат |
|---|---|
| Месяцы 1–2 | literature update, ADR/RQ freeze, profiling executor |
| Месяцы 3–4 | B0/A0 audit, locality traces, scaling baseline |
| Месяцы 5–6 | B1/B2 и exact gates |
| Месяц 7 | C1/C2 и 48-cell core pilot |
| Месяц 8 | C4/C5 и 27-cell accelerator screening |
| Месяц 9 | freeze и core final; C3H/C6 go/no-go |
| Месяц 10 | robustness, representations, scaling |
| Месяц 11 | thesis/article/replication bundle |
| Месяц 12 | clean-room reproduction и резерв |

## 12. Текущая readiness boundary

Repository ready означает готовность к реализации Stage 3A, а не к запуску
pilot/final. До исполнения требуются candidate commits, environment locks,
full-trajectory/endpoint gates, fallback tests и отдельный freeze.

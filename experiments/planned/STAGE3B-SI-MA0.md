# Stage 3B `SI-MA0` — атрибуция механизма и стоимости `state_inference`

[English version](STAGE3B-SI-MA0_EN.md)

## Статус

Протокол заморожен до создания исполняемой реализации и до первого controlled smoke.

Этот пакет регистрирует этап A8 основного сценария A: модельную атрибуцию
механизма и стоимости канонического `Strict.state_inference`. Он не изменяет
запечатанные реализации и evidence предыдущих барьеров, не запускает
эксперимент и не разрешает управление вычислением.

Contract id:

```text
stage3b-si-ma0-v1
```

## Зарегистрированная отправная точка

- base commit: `30de25c50a970fcdb8038fe1ce20273f5efb9b3c`;
- A1 mechanism-controls implementation:
  `69455e6e77e447ff72609d1c8af5fa6136a7e88a`;
- A1 mechanism-controls evidence:
  `474ce9fcac73ff53565f8da91da5688d72b6f475`;
- A1 evidence tag: `stage3b-a1-mechanism-controls-evidence-v1`;
- A1 decision:
  `results/stage-3/a1-mechanism-controls/confirmatory/mechanism-controls-decision.json`;
- Torch2PC commit:
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

До любого controlled execution runner обязан проверить:

```text
mechanism_controls_confirmatory_passed = true
core_controls_passed = true
si_ma0_open = true
```

а также checksum запечатанного A1 evidence.

## Исследовательский вопрос

Можно ли на реальном model-level пути `Strict.state_inference`:

1. разложить наблюдаемую поправку состояния на зарегистрированные
   канонические каналы `PC-CATM`;
2. восстановить наблюдаемую поправку из этих каналов в пределах заранее
   заданной численной погрешности;
3. показать, что наблюдение не меняет состояния, потери и градиенты;
4. связать каждый слой и проход с совместимыми версиями состояния и якобиана;
5. замкнуть учёт времени `state_inference` по зарегистрированным областям;
6. описать распределение времени, VJP, сохранённых тензоров, времени жизни
   графа и синхронизации между механизмами?

## Роль пакета

`SI-MA0` является validity-and-attribution gate.

Положительный результат разрешает model-level пассивную диагностику
`NCZ`/`ECZ`/`TNZ` и последующие отдельные проверки B1/B2. Он сам по себе не
подтверждает:

- частоту или устойчивость диагностических классов в обучении;
- полезность признаков для решения о следующем exact sweep;
- возможность пропуска sweep или слоя;
- ускорение `Strict`;
- достаточность диагностического фактор-пространства;
- причинный эффект `QWake-PC`;
- превосходство predictive coding над BP.

## Зарегистрированный объект

### Модель и checkpoints

```text
dataset = FashionMNIST
split = validation
architecture = lenet_classic
method = Strict
checkpoint = final
model_seeds = 0..9
dtype = float32
device = ROCm
eta = 0.05
inference_steps = 20
batch_size = 256
validation_batch_ids = 0,1,2
shuffle = false
loader_workers = 0
optimizer_step = disabled
parameter_update = disabled
```

Используются существующие финальные checkpoints Stage 2. Модель не
переобучается. Перед каждым наблюдаемым запуском checkpoint и входное состояние
восстанавливаются заново.

Loader тестовой выборки не создаётся:

```text
dataset_loader_used = true
test_split_access = false
```

Для каждого batch сохраняются hash входов, targets, индексов примеров,
checkpoint, разрешённой конфигурации и split manifest.

### Независимая статистическая единица

Независимая единица — отдельно обученная модель, заданная `model_seed`.

Batch, слой, sweep, канал, VJP, сохранённый tensor и техническое повторение
являются вложенными наблюдениями и не трактуются как независимые модели.

## Execution lanes и scopes

### Smoke

Инженерная проверка выполняется после фиксации implementation commit:

```text
CPU Docker: model_seed=0, validation_batch_id=0
ROCm Docker: model_seed=0, validation_batch_id=0
```

Smoke проверяет schema, полноту полей, численную реконструкцию, отсутствие
доступа к test split и работоспособность таймеров. Smoke не входит в
confirmatory evidence и не используется для изменения threshold.

### Confirmatory

Основной confirmatory lane:

```text
controlled Docker/ROCm
model_seeds = 0..9
validation_batch_ids = 0,1,2
```

После первого controlled confirmatory output запрещены:

- retuning threshold;
- замена model seed или batch;
- удаление finite или nonfinite record;
- выбор повторения по результату;
- изменение состава областей;
- изменение определения канонического канала.

## Зарегистрированные observer modes

Для идентичного checkpoint и batch выполняются:

```text
no_hooks
instrumented_disabled
counters_only
tensor_summaries
full_attribution
```

`no_hooks` является численным reference.

Все modes используют одинаковые веса, входы, targets, RNG snapshots, `eta`,
число sweeps, порядок слоёв и начальное belief state. Сериализация выполняется
после завершения измеряемого участка.

Основная атрибуция времени областям выполняется в `counters_only`.
`tensor_summaries` и `full_attribution` используются для механизмной
реконструкции и измерения overhead, но их абсолютное время не подменяет время
канонического пути.

## Декомпозиция `state_inference`

Зарегистрированы семь взаимоисключающих областей:

```text
inference_setup
lower_prediction_and_error
upper_state_vjp
component_aggregation
belief_update
sweep_bookkeeping
inference_finalize
```

Определения:

- `inference_setup` — создание начальных belief states и структур одного
  вызова, исключая dataset loading и checkpoint loading;
- `lower_prediction_and_error` — локальное предсказание, ошибка собственного
  слоя, применение precision operator и формирование `c_self`;
- `upper_state_vjp` — вычисление перенесённого верхнего вклада `c_upper`
  посредством state VJP;
- `component_aggregation` — группировка технических частей по canonical
  channel id, вычисление суммы каналов и показателей геометрии;
- `belief_update` — применение уже вычисленной поправки к belief state;
- `sweep_bookkeeping` — индексы sweep/layer, version counters, convergence
  fields и обязательная управляющая bookkeeping без принятия adaptive
  решения;
- `inference_finalize` — завершение вызова, финальные consistency checks и
  подготовка возвращаемого объекта до сериализации.

Ни одна операция measured `state_inference` не может одновременно
принадлежать двум областям. Неатрибутированный остаток сохраняется отдельно и
не перераспределяется.

## Канонический layer-sweep event

На каждом `(model_seed, batch_id, sweep_index, layer_index)` сохраняются:

```text
contract_id
source_git_commit
experiment_image
image_revision
torch_version
torch_hip_version
torch2pc_commit
checkpoint_sha256
config_sha256
split_manifest_sha256
input_sha256
target_sha256
model_seed
batch_id
sweep_index
layer_index
observer_mode
state_version_before
state_version_after
jacobian_version
canonical_channel_ids
c_self_norm
c_upper_norm
A
R
chi
Q
P
N
D
source_error_norm
transported_upper_norm
gamma
transport_status
observed_update_norm
reconstructed_update_norm
absolute_l2
relative_l2
max_abs
cosine
state_transition_absolute_l2
state_transition_relative_l2
state_transition_max_abs
state_transition_cosine
vjp_call_count
saved_tensor_count
saved_tensor_bytes
graph_birth_event
graph_release_event
synchronization_count
finite
passed
```

Неприменимые значения записываются как `null`.

## Реконструкция поправки

Для каждого события реализация обязана экспортировать:

```text
u_observed
```

— tensor, фактически переданный в канонический update map до изменения belief
state.

Из зарегистрированных canonical channels независимо строится:

\[
u_l^{(\mathrm{reconstructed})}
  = c_l^{(\mathrm{self})} + c_l^{(\mathrm{upper})}.
\]

Технические части сначала группируются по canonical channel id. Они не
считаются дополнительными причинными каналами.

Главный барьер:

\[
u_l^{(\mathrm{reconstructed})}
  \approx u_l^{(\mathrm{observed})}.
\]

Отдельно проверяется state transition:

```text
h_after ≈ canonical_update_map(h_before, u_observed, eta)
```

Знак и масштаб update не выводятся из диагностического кода: используется тот
же frozen update map, что и в канонической реализации `Strict`.

## Численные thresholds

Для ROCm/float32 наследуется implementation-snapshot profile A1:

```text
zero_atol = 1e-6
max_relative_l2 = 1e-3
max_abs = 1e-5
min_cosine = 0.999
```

Zero-safe rule:

1. если обе нормы не превышают `zero_atol`, сравнение выполняется по
   `max_abs`, а cosine записывается как `null`;
2. если zero-like только один tensor, record завершается как failed;
3. NaN или infinity всегда завершают record как failed.

CPU smoke использует A1 CPU/float64 thresholds и не определяет confirmatory
решение.

## Sub-gates

### `REC-MA0` — reconstruction gate

Проходит, если на всех 3600 confirmatory layer-sweep events:

```text
10 model seeds * 3 batches * 20 sweeps * 6 layers = 3600
```

выполнены:

- полный набор двух canonical channels;
- `u_reconstructed ≈ u_observed`;
- state transition equivalence;
- finite values;
- отсутствие duplicate event keys;
- отсутствие missing mandatory fields;
- корректный zero-safe path.

Любой failed reconstruction event завершает `REC-MA0` как failed.

До прохождения `REC-MA0` model-level labels `NCZ` и `ECZ` не
интерпретируются.

### `OBS-MA0` — non-interference gate

Для каждого из 150 сочетаний:

```text
10 model seeds * 3 batches * 5 observer modes = 150
```

с `no_hooks` сравниваются:

- финальные belief states;
- loss;
- parameter gradients после state inference;
- model-state fingerprint;
- input/target fingerprint;
- RNG fingerprint после разрешённых deterministic operations.

`instrumented_disabled`, `counters_only`, `tensor_summaries` и
`full_attribution` должны пройти implementation-snapshot thresholds.

Величина overhead каждого mode публикуется, но высокий overhead сам по себе не
является причиной численного fail.

### `VER-MA0` — state/Jacobian version gate

Проходит, если:

- version fields присутствуют на каждом event;
- `state_version_after = state_version_before + 1` для каждого belief update;
- state versions монотонны внутри layer;
- Jacobian version соответствует фактически использованному snapshot;
- один channel record не объединяет несовместимые версии;
- snapshot fingerprint совпадает между reconstruction branches;
- ordering sweep и layer соответствует frozen `Strict`.

### `COST-MA0` — accounting gate

Основное device-time измерение использует:

```text
warmup_steps = 20
timing_repetitions = 5
measured_steps_per_repetition = 50
```

Перед каждым measured step восстанавливается одинаковое начальное belief
state; параметры не обновляются.

ROCm events записываются без per-region device synchronization. Разрешена одна
обязательная синхронизация в конце repetition для чтения всех event durations.
Каждая дополнительная синхронизация фиксируется.

Для каждого measured step сохраняются:

- total `state_inference` device time;
- exclusive device time каждой из семи областей;
- wall time;
- synchronization count;
- VJP count;
- peak allocated/reserved memory;
- finite flag.

Ожидаемые raw counts для `counters_only`:

```text
total timing records:
10 * 3 * 5 * 50 = 7500

region timing records:
10 * 3 * 5 * 50 * 7 = 52500
```

Accounting residual:

\[
\rho =
\frac{
  \left|t_{\mathrm{total}}-\sum_r t_r\right|
}{
  \max(t_{\mathrm{total}}, 10^{-12})
}.
\]

`COST-MA0` проходит, если:

```text
rho <= 0.05
```

для не менее 99% measured steps и для 100% repetition-level aggregates, все
times finite и nonnegative, а отсутствующие шаги равны нулю.

Шаги с `rho > 0.05` сохраняются. Threshold не изменяется после просмотра
данных.

### `CMP-MA0` — completeness and provenance gate

Проходит, если:

- присутствуют все 10 model seeds и 3 batch ids;
- все ожидаемые layer-sweep и timing records присутствуют;
- все attempts сохранены;
- checkpoint/config/input/target hashes проверены;
- source commit и image digest immutable;
- test split не использовался;
- dataset loading находится вне measured region;
- SHA256 manifests проходят проверку;
- contract JSON в output побайтно совпадает с frozen contract реализации,
  кроме заранее зарегистрированных runtime provenance fields.

## Итоговый gate

```text
si_ma0_passed =
    prerequisites_verified
    and REC-MA0
    and OBS-MA0
    and VER-MA0
    and COST-MA0
    and CMP-MA0
```

Решения:

```text
pass:
  все sub-gates true

fail:
  хотя бы один scientific/contract sub-gate false при полном evidence

inconclusive:
  evidence неполон из-за документированной инфраструктурной причины и
  scientific fail не установлен
```

`inconclusive` не разрешает интерпретацию `NCZ`/`ECZ` и не открывает следующий
этап.

## Primary estimands

### Механизмная валидность

На уровне event:

- relative L2 и max-abs reconstruction error;
- relative L2 и max-abs state-transition error;
- доля passed events;
- число nonfinite, missing и duplicate records.

Это all-events gate, а не статистическая проверка среднего.

### Атрибуция стоимости

Для model seed `m` и области `r`:

\[
s_{m,r}
=
\frac{\sum t_{m,r}}
     {\sum t_{m,\mathrm{state\_inference}}}.
\]

Суммирование сначала выполняется по batch, repetition и measured step внутри
одной модели.

Между моделями публикуются:

- значения всех десяти `s_{m,r}`;
- median;
- IQR;
- среднее;
- 95% bootstrap confidence interval с resampling только по `model_seed`;
- fixed bootstrap seed `20260715`;
- `10000` bootstrap repeats.

Не регистрируется требование, что конкретная область обязана быть
доминирующей. Нулевой, смешанный или seed-dependent результат публикуется без
замены estimand.

### Secondary diagnostics

Отдельно публикуются:

- device/wall-time overhead observer modes;
- VJP counts по layer и sweep;
- saved-tensor count и bytes;
- graph lifetime в event-index units;
- synchronization count;
- correction geometry и transport summaries;
- распределение accounting residual;
- memory allocation summaries.

Secondary diagnostics не используются для переопределения `si_ma0_passed`,
кроме явно зарегистрированных completeness, finite и accounting checks.

## Multiplicity

`SI-MA0` не регистрирует семейство нулевых статистических гипотез. Primary
validity criteria являются deterministic all-record gates.

Любые будущие inferential comparisons механизмных признаков, diagnostic
quotients, predictor utility или B1/B2 требуют отдельной preregistration и
собственной multiplicity policy.

## Attempts и rerun policy

Каждая попытка получает immutable `attempt_id`.

Разрешён повтор только после:

- сохранения failed attempt;
- классификации причины как infrastructure failure;
- неизменности source commit, image, contract, seed, batch и checkpoint;
- записи связи replacement attempt с исходной попыткой.

Scientific failure, nonfinite tensor, reconstruction mismatch, высокий
accounting residual или неудобный cost profile не являются причиной удаления
или замены попытки.

## Зарегистрированные outputs

Рабочие результаты:

```text
results/stage-3/si-ma0/working/
```

Будущий confirmatory evidence:

```text
results/stage-3/si-ma0/confirmatory/
```

Обязательные артефакты:

```text
si_ma0_contract.json
si_ma0_attempts.jsonl
si_ma0_environment.json
si_ma0_event_records.csv
si_ma0_mode_comparisons.csv
si_ma0_total_timing_records.csv
si_ma0_region_timing_records.csv
si_ma0_vjp_records.csv
si_ma0_saved_tensor_records.csv
si_ma0_graph_lifetime_records.csv
si_ma0_batch_summaries.csv
si_ma0_model_region_summaries.csv
si_ma0_summary.json
si_ma0_decision.json
SHA256SUMS
```

Raw tensors могут сохраняться в NPZ вне Git, но их manifest и hashes входят в
evidence.

## Границы допустимого вывода

При `si_ma0_passed=true` допустимо утверждать:

> На зарегистрированных финальных `Strict` checkpoints FashionMNIST,
> controlled ROCm lane и фиксированных validation batches наблюдаемая
> state-inference поправка воспроизводится зарегистрированными каналами
> `PC-CATM`, наблюдение численно невозмущающее, версии согласованы, а стоимость
> вызова замкнута по заранее заданным областям в пределах accounting threshold.

Нельзя утверждать:

- что эти доли времени универсальны для других моделей, batch sizes, devices
  или checkpoints;
- что `NCZ`, `ECZ` или `TNZ` разрешают пропуск вычисления;
- что механизмные labels предсказывают endpoint-gradient utility;
- что сокращение VJP даст пропорциональное ускорение;
- что найдено минимальное достаточное фактор-пространство;
- что active control безопасен.

## Разделение этапов

Этот preregistration commit содержит только:

```text
experiments/planned/STAGE3B-SI-MA0.md
experiments/planned/STAGE3B-SI-MA0_EN.md
experiments/planned/STAGE3B-SI-MA0-CONTRACT.json
```

Исполняемая реализация, smoke, confirmatory execution, анализ и evidence
создаются отдельными commits и ветками.

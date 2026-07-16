# Stage 3B A1 — OBS-OH0: overhead пассивного наблюдателя

## Статус

Протокол заморожен. Реализация benchmark runner и экспериментальные результаты отсутствуют.

OBS-OH0 открывается только после успешного прохождения, запечатывания и публикации OBS-NI0.

## Зарегистрированная отправная точка

- repository evidence commit: `f80d070d79982f6420dce00d504c60dbdf1abc1b`;
- OBS-NI0 implementation commit: `3cbda083bc5747732a51295da9a4494ffde48436`;
- OBS-NI0 tag: `stage3b-a1-obs-ni0-v1`;
- passive-observer schema: `stage3b-a1-obs-ni0-first-forward-io-v1`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

Запечатанные EQ-S0, EQ-S1, EQ-S2 и OBS-NI0 evidence являются immutable prerequisites.

## Исследовательский вопрос

Каковы runtime и memory overhead зарегистрированного passive observer относительно идентичного execution path с выключенным observer для:

1. iterative FixedPred;
2. joint-VJP reduced shortcut?

Дополнительный инженерный вопрос: остаётся ли overhead внутри заранее зарегистрированного бюджета, достаточного для перехода к SI-MA0?

## Роль OBS-OH0

OBS-OH0 является bounded-overhead control.

Он не проверяет вычислительную неинтерферентность observer: она уже проверена OBS-NI0. Он не утверждает, что observer имеет нулевую стоимость. Положительный результат означает, что стоимость зарегистрированного observer измерена валидно и находится внутри зарегистрированного инженерного бюджета в зарегистрированной среде и выборке.

OBS-OH0 не оценивает:

- полезность captured signals;
- механизмную интерпретацию payload;
- full-training overhead;
- overhead stateful optimizers;
- overhead других architectures или batch sizes;
- active observer и intervention logic;
- causal validity PC-CATM.

## Замороженный объект измерения

Измеряется только observer, запечатанный в OBS-NI0:

- schema id: `stage3b-a1-obs-ni0-first-forward-io-v1`;
- верхнеуровневые слои: `6`;
- roles: `layer_input`, `layer_output`;
- capture policy: первый forward invocation каждого верхнеуровневого слоя;
- records на observer-on execution: `12`;
- payload copy: `tensor.detach().clone()`;
- последующие forward invocations считаются, но повторно не захватываются;
- observer lifecycle завершается удалением всех зарегистрированных hooks.

Изменение schema, capture points, payload roles, copy policy или cleanup policy требует нового preregistration и нового evidence version.

## Сравниваемые arms

### Arm A — iterative FixedPred

Reference:

- iterative FixedPred;
- `eta = 1`;
- `inference_steps = len(model) = 6`;
- feed-forward initialization;
- observer disabled.

Candidate:

- тот же iterative FixedPred;
- идентичные `eta`, inference steps и initialization;
- passive observer enabled.

### Arm B — joint-VJP reduced shortcut

Reference:

- opt-in joint-VJP reduced shortcut;
- один joint state-and-parameter VJP на верхнеуровневый слой;
- observer disabled.

Candidate:

- тот же joint-VJP reduced shortcut;
- passive observer enabled.

Canonical BP, FixedPred, Strict и joint-VJP implementations не изменяются.

## Benchmark schema freeze

Implementation source commit до первого controlled smoke должен зафиксировать:

- постоянный `benchmark_schema_id = stage3b-a1-obs-oh0-v1`;
- точный measured-region contract;
- ordered execution records;
- paired-order rule;
- warm-up policy;
- timing-repeat count;
- memory-worker protocol;
- device-synchronization policy;
- metric units;
- aggregation rules;
- pass criteria;
- output schemas;
- provenance checks;
- unit tests.

После первого controlled execution benchmark schema не изменяется без нового source commit и нового preregistered evidence version.

## Общий paired-execution contract

Каждая observer-off / observer-on пара использует:

- идентичный исходный model `state_dict`;
- отдельный свежий model clone для каждого execution;
- идентичный input batch и targets;
- идентичную loss function и reduction;
- идентичный dtype и device;
- идентичный model mode;
- идентичный RNG snapshot;
- идентичный Torch2PC checkout;
- идентичный controlled Docker image;
- идентичную CPU thread configuration;
- отсутствие disk writes и console logging внутри measured region.

Input batch загружается до paired snapshot. Model cloning, device transfer, input loading, result validation, DataFrame construction и serialization находятся вне measured region.

Перед каждым paired execution восстанавливаются:

- Python RNG state;
- NumPy RNG state;
- PyTorch CPU RNG state;
- ROCm RNG state для всех доступных devices.

## Разделение timing и memory phases

Runtime и memory измеряются в раздельных phases.

Причина: RSS sampler, allocator queries, peak-stat resets и memory diagnostics сами создают overhead и не должны входить в primary timing estimand.

### Timing phase

Timing phase содержит только matched observer lifecycle и вычислительный path.

### Memory phase

Memory phase выполняется отдельными isolated worker processes и не используется для runtime inference.

Timing records и memory records не объединяются в одну оценку времени.

## Timing measured-region contract

Для каждого execution:

1. model clone, inputs и targets полностью подготовлены;
2. gradients очищены;
3. paired RNG snapshot восстановлен;
4. для ROCm выполняется внешняя `torch.cuda.synchronize()`;
5. фиксируется `start_ns = time.perf_counter_ns()`;
6. reference входит в matched no-op observer context либо candidate регистрирует passive-observer hooks;
7. выполняется только зарегистрированный backward path соответствующего arm;
8. context закрывается; candidate удаляет hooks;
9. для ROCm выполняется внешняя `torch.cuda.synchronize()`;
10. фиксируется `end_ns = time.perf_counter_ns()`.

Primary elapsed time:

```text
elapsed_ns = end_ns - start_ns
```

В measured region включаются:

- observer setup;
- tensor capture и detached clone;
- observer cleanup;
- соответствующий FixedPred либо joint-VJP backward path.

В measured region не включаются:

- dataloader;
- model construction или deepcopy;
- device transfer;
- optimizer construction;
- `optimizer.step()`;
- endpoint comparison;
- payload validation;
- CPU transfer;
- serialization;
- disk I/O;
- benchmark-summary calculation.

`optimizer.step()` исключается, поскольку observer уже закрыт и одинаковая дополнительная работа искусственно уменьшила бы относительный overhead.

## ROCm synchronization policy

ROCm kernels и copies должны быть завершены до чтения end timestamp.

`torch.cuda.synchronize()` вызывается симметрично:

- непосредственно перед `start_ns`;
- непосредственно перед `end_ns`.

Synchronization не вызывается внутри observer hooks и не считается observer operation. Она является внешней benchmark boundary и применяется одинаково к observer-off и observer-on executions.

## Timing warm-up policy

Warm-up выполняется на:

- model seed `0`;
- batch index `0`;
- отдельно для каждого lane и arm.

Зарегистрированное число untimed paired warm-up repetitions:

- smoke: `1` pair на lane и arm;
- confirmatory: `3` pairs на lane и arm.

Warm-up использует ту же alternating-order policy, но его records:

- помечаются как `warmup`;
- не входят в aggregate estimands;
- не входят в pass criteria.

Дополнительное discretionary исключение measured records не допускается.

## Paired order и drift control

Порядок observer-off / observer-on балансируется детерминированно.

Для каждого `(lane, arm, model_seed, batch_index, repeat_index)`:

```text
parity = model_seed + batch_index + repeat_index + arm_index
```

- при чётном `parity`: observer-off затем observer-on;
- при нечётном `parity`: observer-on затем observer-off.

`arm_index = 0` для FixedPred и `1` для joint-VJP.

Порядок фиксируется в каждом record. Ручное изменение порядка после просмотра результатов не допускается.

## Timing metrics

Для каждой measured pair сохраняются:

- `reference_elapsed_ns`;
- `candidate_elapsed_ns`;
- `runtime_delta_ns`;
- `runtime_ratio`;
- `runtime_overhead_fraction`;
- lane;
- arm;
- model seed;
- batch index;
- repeat index;
- execution order;
- dtype;
- device;
- source commit;
- image identifier;
- Torch2PC commit;
- benchmark schema id;
- observer schema id.

Определения:

```text
runtime_delta_ns = candidate_elapsed_ns - reference_elapsed_ns
runtime_ratio = candidate_elapsed_ns / reference_elapsed_ns
runtime_overhead_fraction = runtime_ratio - 1
```

Оба elapsed values должны быть положительными и конечными.

## Timing aggregation

Model seed является независимой экспериментальной единицей.

Batches и timing repetitions являются повторными инженерными наблюдениями внутри seed и не трактуются как независимые научные единицы.

Для каждого `(lane, arm, seed)` вычисляется median `runtime_ratio` по:

- `10` batches;
- `3` measured paired repetitions на batch;
- `30` paired timing records на seed.

Для каждого `(lane, arm)` primary estimand:

```text
primary_runtime_ratio =
median из трёх seed-level median runtime_ratio
```

Также фиксируются:

- minimum seed-level median;
- maximum seed-level median;
- median absolute `runtime_delta_ns`;
- all raw paired records;
- order-stratified medians для off-first и on-first records.

Среднее арифметическое не является primary runtime estimand. Measured outliers не удаляются.

## Memory phase isolation

Каждый memory execution выполняется в свежем worker process внутри того же controlled image.

До measured region worker:

- загружает registered model и batch;
- создаёт model clone;
- переносит tensors на registered device;
- восстанавливает RNG state;
- стабилизирует device;
- фиксирует baseline memory.

Process startup, imports, model construction, data loading и device transfer исключаются из incremental memory metrics.

Observer-off и observer-on memory executions выполняются в отдельных свежих workers с одинаковыми metadata.

## Payload memory accounting

Для candidate execution вычисляется точный retained payload size:

```text
payload_bytes =
sum(tensor.numel() * tensor.element_size())
```

Payload bytes считаются по captured detached tensors до их release.

Также фиксируются:

- records count;
- bytes на role;
- bytes на layer;
- dtype;
- source device;
- shape metadata.

Ожидается ровно `12` payload records на observer-on memory execution.

## CPU memory metrics

CPU worker использует Linux `/proc/self/status`.

Фиксируются:

- baseline `VmRSS`;
- sampled peak `VmRSS` во время measured region;
- final `VmRSS` до release payload;
- `VmHWM` как diagnostic process-level value;
- `incremental_peak_rss_bytes`;
- `incremental_final_rss_bytes`.

Dedicated sampler читает `VmRSS` с interval не более `1 ms`.

Определения:

```text
incremental_peak_rss_bytes =
max(0, sampled_peak_rss_bytes - baseline_rss_bytes)

incremental_final_rss_bytes =
max(0, final_rss_bytes - baseline_rss_bytes)
```

CPU RSS является allocator- и page-sensitive metric. Поэтому exact payload bytes являются primary CPU memory cost, а RSS используется как bounded secondary diagnostic.

## ROCm memory metrics

ROCm worker перед measured region:

1. выполняет `torch.cuda.synchronize()`;
2. фиксирует current allocated и reserved bytes;
3. вызывает `torch.cuda.reset_peak_memory_stats()`;
4. выполняет measured region;
5. выполняет `torch.cuda.synchronize()`;
6. считывает peak allocated и peak reserved bytes.

Фиксируются:

- baseline allocated bytes;
- baseline reserved bytes;
- peak allocated bytes;
- peak reserved bytes;
- current allocated bytes до release payload;
- current reserved bytes до release payload;
- incremental peak allocated bytes;
- incremental peak reserved bytes.

Определения:

```text
incremental_peak_allocated_bytes =
max(0, peak_allocated_bytes - baseline_allocated_bytes)

incremental_peak_reserved_bytes =
max(0, peak_reserved_bytes - baseline_reserved_bytes)
```

`max_memory_allocated` является primary ROCm allocator metric. Reserved-memory delta является secondary diagnostic из-за caching allocator granularity.

## Memory aggregation

Для confirmatory memory phase выполняется одна isolated observer-off / observer-on pair для каждого:

- lane;
- arm;
- model seed;
- batch index.

На каждом lane:

- `3` seeds;
- `10` batches на seed;
- `2` arms;
- `60` paired memory records.

По двум lanes:

- `120` paired memory records.

Для каждого `(lane, arm, seed)` вычисляются median:

- payload bytes;
- observer-on minus observer-off incremental peak memory;
- memory-accounting residual.

Primary memory summaries являются median из трёх seed-level medians. Raw records сохраняются полностью.

## Зарегистрированный runtime budget

Для каждого lane и arm одновременно должны выполняться:

```text
primary_runtime_ratio <= 1.25
max_seed_median_runtime_ratio <= 1.35
```

Это соответствует:

- primary median overhead не выше `25%`;
- ни один seed-level median overhead не выше `35%`.

Отдельный measured repeat не используется как самостоятельный fail threshold из-за scheduler и clock noise.

Budget применяется отдельно к:

- CPU FixedPred;
- CPU joint-VJP;
- ROCm FixedPred;
- ROCm joint-VJP.

## Зарегистрированный memory budget

Для каждого observer-on execution:

```text
payload_bytes <= 67_108_864
```

То есть retained payload не превышает `64 MiB`.

### CPU bound

Для каждого `(arm, seed)`:

```text
median(candidate_incremental_peak_rss
       - reference_incremental_peak_rss)
<=
median(payload_bytes) + max(8 MiB, 0.25 * median(payload_bytes))
```

### ROCm allocated-memory bound

Для каждого `(arm, seed)`:

```text
median(candidate_incremental_peak_allocated
       - reference_incremental_peak_allocated)
<=
median(payload_bytes) + max(1 MiB, 0.10 * median(payload_bytes))
```

Отрицательная paired memory difference допустима как allocator noise и сохраняется без clipping в raw paired metric. Individual incremental metrics остаются non-negative по определению.

ROCm reserved-memory delta и CPU `VmHWM` являются descriptive diagnostics и не имеют hard pass threshold.

## Smoke scope

Canonical smoke выполняется только в controlled Docker image.

Для каждого lane:

- model seeds: `0, 1, 2`;
- batch index: `0`;
- arms: FixedPred и joint-VJP;
- timing warm-up pairs: `1` на arm;
- measured timing pairs: `3` на seed и arm;
- isolated memory pairs: `1` на seed и arm.

На каждом smoke lane ожидается:

- `18` measured timing pairs;
- `36` timed executions;
- `6` memory pairs;
- `12` memory workers.

Smoke предназначен для проверки schema, synchronization, order balancing, worker isolation, metric validity и provenance. Smoke results не входят в confirmatory evidence.

## Confirmatory scope

После успешного smoke для каждого lane:

- model seeds: `0, 1, 2`;
- batches на seed: `10`;
- arms: FixedPred и joint-VJP;
- measured timing pairs на batch и arm: `3`;
- isolated memory pairs на batch и arm: `1`;
- lanes: Docker CPU и Docker/ROCm.

На каждом confirmatory lane ожидается:

- `180` measured timing pairs;
- `360` timed executions;
- `60` memory pairs;
- `120` memory workers.

По двум lanes ожидается:

- `360` measured timing pairs;
- `720` timed executions;
- `120` memory pairs;
- `240` memory workers.

## Correctness guard

Перед timing и memory benchmark для каждого `(lane, arm, seed, batch)` выполняется untimed guard pair.

Guard должен подтвердить:

- endpoint gradients соответствуют OBS-NI0 threshold policy;
- observer schema полна;
- records count равен `12`;
- hooks удалены;
- payload detached и finite;
- source commit одинаков;
- Torch2PC revision одинаков;
- RNG state не изменён observer;
- model buffers и inputs не изменены.

Guard failure завершает lane как failed. Guard execution не входит в overhead metrics.

## Provenance contract

Каждый output фиксирует:

- full source Git commit;
- controlled image identifier;
- image revision label;
- branch;
- benchmark schema id;
- observer schema id;
- Torch2PC commit;
- PyTorch version;
- HIP version;
- lane;
- device name;
- dtype;
- CPU thread count;
- visible ROCm devices;
- model architecture;
- batch size;
- model seeds;
- batch indices;
- timing repetitions;
- warm-up count;
- sampler interval.

CPU и ROCm confirmatory outputs должны ссылаться на один source commit и одну benchmark schema.

Compose runner обязан явно передавать verified:

- `SOURCE_GIT_COMMIT`;
- `EXPERIMENT_IMAGE`.

Унаследованные shell environment values не могут переопределять verified provenance.

## Pass criteria

OBS-OH0 проходит только при одновременном выполнении всех условий:

- OBS-NI0 seal остаётся checksum-valid;
- benchmark schema зафиксирована до smoke;
- все correctness guards проходят;
- все elapsed values положительны и конечны;
- все memory values являются целыми неотрицательными values там, где это требуется определением;
- все expected timing и memory records присутствуют;
- отсутствуют duplicate record keys;
- paired order соответствует registered parity rule;
- warm-up records исключены из confirmatory aggregation;
- CPU и ROCm provenance подтверждены;
- source commit одинаков для обоих lanes;
- Torch2PC revision одинаков для обоих lanes;
- observer schema совпадает с sealed OBS-NI0 schema;
- все четыре lane-arm runtime budgets выполнены;
- payload budget выполнен;
- CPU memory bound выполнен для обоих arms и всех seeds;
- ROCm allocated-memory bound выполнен для обоих arms и всех seeds;
- все confirmatory runs имеют `passed = true`.

## Stop rules

При correctness-guard failure, invalid measurement, missing record, provenance mismatch или превышении зарегистрированного budget:

- OBS-OH0 получает статус `failed`;
- SI-MA0 остаётся закрытым;
- threshold retuning после просмотра результатов не выполняется;
- measured records не удаляются;
- причина исследуется отдельным diagnostic patch;
- observer optimization выполняется отдельным source commit;
- новый confirmatory run требует нового evidence version;
- изменение observer schema требует возврата к OBS-NI0.

OOM, worker crash, non-finite metric или zero/negative elapsed time считаются failed records.

## Поддерживаемое утверждение

Положительный OBS-OH0 поддерживает утверждение, что runtime и retained-memory overhead зарегистрированного passive observer для iterative FixedPred и joint-VJP reduced shortcut остаётся внутри зарегистрированного инженерного бюджета в controlled CPU/ROCm confirmatory sample.

## Граница утверждения

OBS-OH0 не устанавливает:

- нулевой overhead;
- full-training overhead;
- overhead stateful optimizers;
- overhead других models, batch sizes или devices;
- полезность или интерпретируемость payload;
- causal validity PC-CATM;
- universal production suitability.

Runtime и memory results относятся только к зарегистрированной архитектуре, batch size, observer schema, software revision и controlled hardware lanes.

## Evidence policy

Рабочие outputs сохраняются в игнорируемом каталоге `working/`.

После успешного confirmatory control создаётся отдельный immutable package:

- CPU timing records и summaries;
- CPU memory records и summaries;
- ROCm timing records и summaries;
- ROCm memory records и summaries;
- benchmark schema manifest;
- observer schema reference;
- provenance manifest;
- bounded claim;
- SHA-256;
- отдельный evidence commit;
- annotated tag `stage3b-a1-obs-oh0-v1`.

Sealed EQ-S0, EQ-S1, EQ-S2 и OBS-NI0 evidence не изменяются.

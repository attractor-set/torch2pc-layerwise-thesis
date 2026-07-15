# Stage 3B A1 — OBS-NI0: неинтерферентность пассивного наблюдателя

## Статус

Протокол заморожен. Реализация пассивного наблюдателя и экспериментальные результаты отсутствуют.

## Предшествующие equivalence gates

OBS-NI0 открывается только после успешного запечатывания:

- EQ-S0: BP против iterative FixedPred;
- EQ-S1: BP против joint-VJP reduced shortcut;
- EQ-S2: iterative FixedPred против joint-VJP reduced shortcut.

Зарегистрированная отправная точка:

- repository commit: `826d8666c2d38b011253582c84abd7f0fdeb916e`;
- EQ-S0 tag: `stage3b-a1-eq-s0-v1`;
- EQ-S1 tag: `stage3b-a1-eq-s1-v1`;
- EQ-S2 tag: `stage3b-a1-eq-s2-v1`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

## Исследовательский вопрос

Изменяет ли включение пассивного наблюдателя endpoint gradients, параметры после одного optimizer step, optimizer state, model buffers или RNG state относительно идентичного исполнения с выключенным наблюдателем?

## Роль OBS-NI0

OBS-NI0 проверяет только вычислительную неинтерферентность наблюдателя.

Положительный результат означает, что зарегистрированный passive observer не изменил проверяемые endpoints в зарегистрированной среде и на зарегистрированной выборке.

OBS-NI0 не оценивает:

- полезность собранных сигналов;
- корректность механизмной интерпретации;
- runtime overhead;
- memory overhead;
- full training trajectory;
- active observer или intervention logic.

Runtime и memory overhead относятся к отдельному gate OBS-OH0.

## Observer contract

Пассивный наблюдатель является read-only instrumentation layer.

Во время наблюдаемого execution path он:

- не изменяет model parameters;
- не изменяет model buffers;
- не изменяет optimizer state;
- не изменяет input tensors;
- не изменяет computation graph;
- не вызывает `backward()`;
- не вызывает дополнительные `torch.autograd.grad`;
- не вызывает `optimizer.step()`;
- не использует in-place операции над наблюдаемыми тензорами;
- не вызывает случайные операции;
- не использует наблюдаемые значения для управления вычислительным путём.

Захват tensor payload выполняется как detached copy:

    captured = tensor.detach().clone()

Во время наблюдаемого forward/reverse path observer не вызывает для payload:

- `.item()`;
- `.numpy()`;
- `.cpu()`;
- синхронизацию устройства, добавленную специально для логирования;
- запись на диск.

Перемещение payload на CPU и сериализация разрешаются только после завершения наблюдаемого вычислительного пути.

## Observer schema freeze

Точный набор capture points и payload roles фиксируется в implementation source commit до первого controlled smoke run.

Implementation source commit должен содержать:

- постоянный `observer_schema_id`;
- упорядоченный список ожидаемых payload roles;
- ожидаемое число records на слой и run;
- правила именования layer и tensor records;
- правила cleanup;
- unit tests структурной полноты.

После первого controlled execution schema не изменяется без нового source commit и нового preregistered evidence version.

OBS-NI0 использует payload только для проверки структуры и passive-observer contract. Научная интерпретация payload в этом gate не выполняется.

## Сравниваемые arms

### Arm A — iterative FixedPred

Reference:

- iterative FixedPred;
- `eta = 1`;
- `inference_steps = len(model)`;
- feed-forward initialization;
- observer disabled.

Candidate:

- тот же iterative FixedPred;
- те же `eta`, inference steps и initialization;
- passive observer enabled.

### Arm B — joint-VJP reduced shortcut

Reference:

- opt-in joint-VJP reduced shortcut;
- один joint state-and-parameter VJP на верхнеуровневый слой;
- observer disabled.

Candidate:

- тот же joint-VJP reduced shortcut;
- passive observer enabled.

Canonical BP, FixedPred и Strict implementations не изменяются.

## Paired-execution contract

Каждая reference/candidate пара использует:

- идентичный исходный model `state_dict`;
- отдельные model clones;
- идентичный input batch;
- идентичные targets;
- идентичную loss function и reduction;
- идентичный dtype;
- идентичный device;
- идентичный training/evaluation mode;
- идентичные model buffers;
- идентичную optimizer configuration;
- отдельные optimizer instances;
- идентичный RNG snapshot перед каждым paired path.

Перед reference execution сохраняются:

- Python RNG state;
- NumPy RNG state;
- PyTorch CPU RNG state;
- ROCm RNG state для всех доступных devices.

Тот же snapshot восстанавливается перед candidate execution.

Input batch формируется до сохранения paired RNG snapshot и повторно не загружается между reference и candidate.

## Endpoint comparisons

Для каждого arm сравниваются:

1. именованные parameter gradients;
2. параметры после одного идентичного optimizer step;
3. tensor optimizer state;
4. scalar optimizer state;
5. model buffers;
6. post-execution Python RNG state;
7. post-execution NumPy RNG state;
8. post-execution PyTorch CPU RNG state;
9. post-execution ROCm RNG state;
10. observer lifecycle cleanup.

Optimizer:

- SGD;
- learning rate `0.001`;
- momentum `0.0`.

При `momentum = 0.0` tensor optimizer state ожидаемо отсутствует. Это ограничение фиксируется в claim boundary.

## Buffer comparison

Наборы именованных buffers должны совпадать точно.

Для floating-point buffers используются lane-specific numerical thresholds.

Для integer, boolean и categorical buffers используется точное равенство.

Отсутствие model buffers является допустимым результатом и явно фиксируется в summary.

## RNG comparison

Observer не должен потреблять RNG.

Post-execution RNG states reference и candidate должны совпадать точно после восстановления одинакового pre-execution snapshot.

ROCm RNG сравнивается отдельно для каждого доступного device.

## Observer payload invariants

Для каждого captured tensor должны выполняться:

- tensor является detached copy;
- `requires_grad = false`;
- `grad_fn is None`;
- значение конечно;
- shape соответствует зарегистрированной schema;
- dtype metadata соответствует исходному tensor;
- device metadata соответствует исходному tensor;
- layer identifier присутствует;
- tensor role присутствует;
- record key уникален в пределах run.

После завершения run должны выполняться:

- все ожидаемые capture points представлены;
- отсутствуют duplicate records;
- observer lifecycle закрыт;
- зарегистрированные hooks или handles удалены;
- observer storage не содержит ссылок на live autograd graph.

Нарушение payload invariants считается провалом run независимо от endpoint equivalence.

## Numerical threshold policy

Используется та же lane-specific numerical policy, что в EQ-S0, EQ-S1 и EQ-S2.

### CPU

- dtype: `torch.float64`;
- `min_cosine = 0.99999`;
- `max_relative_l2 = 1e-7`;
- `zero_atol = 1e-12`.

### ROCm

- dtype: `torch.float32`;
- `min_cosine = 0.999`;
- `max_relative_l2 = 1e-3`;
- `zero_atol = 1e-7`.

Пороги не перенастраиваются после просмотра OBS-NI0 результатов.

## Execution scope

Canonical execution выполняется только в контролируемом Docker image.

### Smoke

- model seeds: `0, 1, 2`;
- batches на seed: `1`;
- arms: FixedPred и joint-VJP;
- lanes: Docker CPU и Docker/ROCm.

### Confirmatory control

После успешного smoke:

- model seeds: `0, 1, 2`;
- batches на seed: `10`;
- arms: FixedPred и joint-VJP;
- lanes: Docker CPU и Docker/ROCm.

Model seed является независимой экспериментальной единицей. Batches являются повторными контрольными наблюдениями внутри seed.

## Ожидаемый минимальный объём confirmatory endpoint evidence

На каждом execution lane:

- `30` paired runs для FixedPred arm;
- `30` paired runs для joint-VJP arm;
- `60` paired runs суммарно;
- `600` endpoint-gradient comparisons;
- `600` parameter-after-step comparisons;
- `1200` endpoint tensor comparisons.

По двум lanes:

- `120` paired runs;
- `1200` endpoint-gradient comparisons;
- `1200` parameter-after-step comparisons;
- `2400` endpoint tensor comparisons.

Buffer, RNG и observer-payload records учитываются отдельно и не включаются в эти endpoint totals.

## Pass criteria

OBS-NI0 проходит только при одновременном выполнении всех условий:

- все endpoint tensors конечны;
- все gradient comparisons проходят зарегистрированные thresholds;
- все parameter-after-step comparisons проходят зарегистрированные thresholds;
- optimizer tensor state соответствует;
- optimizer scalar state соответствует;
- model buffer keys и values соответствуют;
- post-execution RNG states соответствуют точно;
- observer payload schema полна;
- все captured tensors detached;
- все payload values конечны;
- отсутствуют duplicate observer records;
- observer cleanup завершён;
- все runs обоих arms имеют `passed = true`;
- CPU provenance подтверждён;
- ROCm provenance подтверждён;
- source commit одинаков для обоих lanes;
- Torch2PC revision одинаков для обоих lanes;
- sealed EQ-S0, EQ-S1 и EQ-S2 evidence остаются checksum-valid.

## Stop rules

При любом failed или non-finite comparison:

- OBS-NI0 получает статус `failed`;
- OBS-OH0 остаётся закрытым;
- SI-MA0 остаётся закрытым;
- observer не включается в canonical execution;
- зарегистрированные thresholds не перенастраиваются;
- причина исследуется отдельным diagnostic patch;
- повторный confirmatory run выполняется только после нового source commit;
- изменённая observer schema требует нового evidence version.

## Поддерживаемое утверждение

Положительный OBS-NI0 поддерживает утверждение, что зарегистрированный passive observer не изменил endpoint gradients, параметры после одного stateless SGD step, optimizer state, model buffers и RNG state для iterative FixedPred и joint-VJP reduced shortcut на зарегистрированной CPU/ROCm выборке.

## Граница утверждения

OBS-NI0 не устанавливает:

- неинтерферентность на протяжении полной training trajectory;
- неинтерферентность для stateful optimizers;
- отсутствие runtime overhead;
- отсутствие memory overhead;
- корректность интерпретации captured signals;
- причинную валидность PC-CATM;
- универсальную применимость вне зарегистрированной архитектуры и среды.

## Evidence policy

Рабочие outputs сохраняются в игнорируемом каталоге `working/`.

После успешного confirmatory control создаётся отдельный immutable package:

- CPU summaries и records;
- ROCm summaries и records;
- observer schema manifest;
- evidence manifest;
- bounded claim;
- SHA-256;
- отдельный evidence commit;
- annotated tag `stage3b-a1-obs-ni0-v1`.

Sealed EQ-S0, EQ-S1 и EQ-S2 evidence не изменяются.

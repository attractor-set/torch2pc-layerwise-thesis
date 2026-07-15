# Stage 3B A1 — EQ-S2: iterative FixedPred против joint-VJP shortcut

## Статус

Протокол заморожен. Реализация EQ-S2 и экспериментальные результаты отсутствуют.

## Исследовательский вопрос

Воспроизводит ли opt-in joint-VJP reduced shortcut endpoint gradients и параметры после одного идентичного шага stateless SGD относительно существующего iterative FixedPred при `eta = 1` и `n = len(model)` в зарегистрированной pinned-среде?

## Роль EQ-S2

EQ-S2 закрывает третью сторону треугольного контроля:

\[
\mathrm{BP}
\overset{\mathrm{EQ-S0}}{\equiv}
\mathrm{iterative\ FixedPred}
\]

\[
\mathrm{BP}
\overset{\mathrm{EQ-S1}}{\equiv}
\mathrm{joint\mbox{-}VJP\ shortcut}
\]

\[
\mathrm{iterative\ FixedPred}
\overset{\mathrm{EQ-S2}}{\equiv}
\mathrm{joint\mbox{-}VJP\ shortcut}
\]

EQ-S2 является прямой проверкой и не полагается только на транзитивный вывод из EQ-S0 и EQ-S1.

## Сравниваемые пути

### Reference

- существующий iterative FixedPred;
- `eta = 1`;
- `inference_steps = len(model)`;
- feed-forward initialization;
- observer mode `no_hooks`;
- instrumentation полностью отключена.

### Candidate

- opt-in joint-VJP reduced shortcut;
- один joint state-and-parameter VJP на каждый верхнеуровневый слой;
- отдельный detached graph island на слой;
- отсутствие `loss.backward()` в candidate;
- отсутствие iterative FixedPred loop в candidate;
- observer mode `no_hooks`;
- instrumentation полностью отключена.

Canonical BP, FixedPred и Strict paths не изменяются.

## Инварианты входного состояния

Reference и candidate используют:

- идентичный исходный `state_dict`;
- идентичный batch;
- идентичную loss function и reduction;
- идентичные dtype и device;
- идентичный optimizer configuration;
- отдельные model clones;
- отдельные optimizer clones;
- одинаковое RNG state там, где оно применимо;
- одинаковый training/evaluation mode;
- одинаковые buffers;
- одинаковую последовательность подготовки входа.

## Endpoint

Основной endpoint:

1. именованные parameter gradients;
2. параметры после одного идентичного optimizer step;
3. tensor optimizer state;
4. scalar optimizer state.

Optimizer:

- SGD;
- learning rate `0.001`;
- momentum `0.0`.

При `momentum = 0.0` tensor optimizer state ожидаемо отсутствует. Это ограничение фиксируется в claim boundary.

## Structural contract candidate

Для текущего `lenet_classic` ожидается:

- `top_level_layers = 6`;
- `joint_vjp_calls = 6`;
- `graph_islands = 6`;
- `parameterized_layers = 5`;
- `parameter_components = 10`;
- `one_call_per_layer = true`;
- `loss_backward_used_by_candidate = false`;
- `iterative_fixedpred_loop_used_by_candidate = false`.

Нарушение structural contract считается провалом run независимо от endpoint metrics.

## Numerical threshold policy

Используется та же зарегистрированная lane-specific policy, что и в EQ-S0 и EQ-S1.

### CPU

- `min_cosine = 0.99999`;
- `max_relative_l2 = 1e-7`;
- `zero_atol = 1e-12`;
- dtype: `torch.float64`.

### ROCm

- `min_cosine = 0.999`;
- `max_relative_l2 = 1e-3`;
- `zero_atol = 1e-7`;
- dtype: `torch.float32`.

Пороги не перенастраиваются после просмотра EQ-S2 результатов.

## Execution scope

Canonical execution выполняется только в контролируемом Docker-образе.

### Smoke

- model seeds `0, 1, 2`;
- `1` batch на seed;
- Docker CPU;
- Docker/ROCm.

### Confirmatory control

После успешного smoke:

- model seeds `0, 1, 2`;
- `10` batches на seed;
- Docker CPU;
- Docker/ROCm.

Model seed остаётся независимой экспериментальной единицей. Batches являются повторными контрольными наблюдениями внутри seed.

## Pass criteria

EQ-S2 проходит только при одновременном выполнении всех условий:

- все сравниваемые тензоры конечны;
- все endpoint-gradient components проходят зарегистрированные lane-specific thresholds;
- все параметры после optimizer step проходят зарегистрированные lane-specific thresholds;
- optimizer state соответствует зарегистрированному stateless SGD contract;
- каждый run имеет `passed = true`;
- candidate structural contract выполнен;
- Docker image provenance совпадает с experiment source commit;
- Torch2PC revision совпадает между execution lanes;
- sealed EQ-S0 и EQ-S1 evidence остаются неизменными.

## Stop rules

При любом failed или non-finite comparison:

- EQ-S2 получает статус `failed`;
- observer controls остаются закрытыми;
- reduced shortcut не включается в canonical execution;
- зарегистрированные thresholds не перенастраиваются;
- причина исследуется отдельным diagnostic patch;
- повторный confirmatory запуск допускается только после нового source commit и отдельного provenance record.

## Поддерживаемое утверждение

Положительный EQ-S2 поддерживает утверждение, что в зарегистрированной pinned-среде iterative FixedPred при `eta = 1` и `n = len(model)` и joint-VJP reduced shortcut дают эквивалентные endpoint gradients и параметры после одного шага stateless SGD на зарегистрированной выборке CPU и ROCm.

## Граница утверждения

EQ-S2 не устанавливает:

- равенство промежуточных hidden-state trajectories;
- эквивалентность полной training trajectory;
- эквивалентность для Adam или momentum SGD;
- runtime benefit;
- memory benefit;
- observer non-interference;
- корректность active QWake;
- универсальную эквивалентность вне зарегистрированной архитектуры и среды.

## Evidence policy

Рабочие outputs сохраняются в игнорируемом каталоге `working/`.

После успешного confirmatory control создаётся отдельный immutable evidence package:

- CPU summary и records;
- ROCm summary и records;
- manifest;
- bounded claim;
- SHA-256;
- отдельный evidence commit;
- annotated tag `stage3b-a1-eq-s2-v1`.

Sealed EQ-S0 и EQ-S1 evidence не изменяются.

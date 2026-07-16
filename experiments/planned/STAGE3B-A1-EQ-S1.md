# Stage 3B A1 — EQ-S1: reduced shortcut

## Статус

Протокол заморожен. Реализация и экспериментальные результаты отсутствуют.

## Исследовательский вопрос

Воспроизводит ли отдельный opt-in reduced shortcut endpoint gradients backpropagation и параметры после одного идентичного шага stateless SGD в зарегистрированной pinned-среде?

## Сравниваемые пути

Reference:

- стандартный backpropagation;
- существующий зарегистрированный BP evaluator;
- observer mode `no_hooks`.

Candidate:

- отдельный reduced-shortcut evaluator;
- собственная точка входа;
- отсутствие вызова reference BP evaluator как готового black box;
- отсутствие вызова полного итеративного FixedPred loop как готового black box;
- canonical BP, FixedPred и Strict paths остаются неизменными.

Итеративный FixedPred не является reference EQ-S1. Его прямое сравнение с reduced shortcut выполняется отдельно в EQ-S2.

## Инварианты

Для reference и candidate используются:

- идентичный исходный `state_dict`;
- идентичный batch;
- идентичная loss function и reduction;
- идентичные dtype и device;
- идентичный optimizer configuration;
- отдельные model и optimizer clones;
- одинаковое RNG state там, где оно применимо;
- полностью отключённая instrumentation;
- observer mode `no_hooks`.

## Endpoint

Основной endpoint:

1. именованные parameter gradients;
2. параметры после одного идентичного optimizer step.

Optimizer:

- SGD;
- learning rate `0.001`;
- momentum `0.0`.

## Numerical threshold policy

Используется та же заранее зафиксированная lane-specific policy, что и в EQ-S0.

CPU:

- `min_cosine = 0.99999`;
- `max_relative_l2 = 1e-7`;
- `zero_atol = 1e-12`.

ROCm:

- `min_cosine = 0.999`;
- `max_relative_l2 = 1e-3`;
- `zero_atol = 1e-7`.

Пороги не перенастраиваются после просмотра результатов EQ-S1.

## Execution scope

Canonical execution выполняется только в контролируемом Docker-образе.

Smoke:

- model seeds `0, 1, 2`;
- `1` batch на seed;
- Docker CPU;
- Docker/ROCm.

Confirmatory control после успешного smoke:

- model seeds `0, 1, 2`;
- `10` batches на seed;
- Docker CPU;
- Docker/ROCm.

Model seed остаётся независимой экспериментальной единицей. Batches являются повторными контрольными наблюдениями внутри seed.

## Pass criteria

EQ-S1 проходит только при одновременном выполнении всех условий:

- все сравниваемые тензоры конечны;
- все endpoint-gradient components проходят зарегистрированные lane-specific thresholds;
- все параметры после optimizer step проходят зарегистрированные lane-specific thresholds;
- каждый run имеет `passed = true`;
- provenance Docker image совпадает с experiment source commit;
- Torch2PC revision совпадает между execution lanes;
- candidate не изменяет canonical BP, FixedPred или Strict behavior.

## Stop rules

При любом failed или non-finite comparison:

- EQ-S1 получает статус `failed`;
- EQ-S2 не открывается;
- observer controls не открываются;
- reduced shortcut не включается в canonical execution;
- выполняется анализ причины без перенастройки зарегистрированных thresholds.

## Claim boundary

Положительный EQ-S1 устанавливает только endpoint-gradient equivalence и equivalence после одного шага stateless SGD в зарегистрированной среде и на зарегистрированной выборке.

EQ-S1 не устанавливает:

- equivalence hidden-state trajectories;
- equivalence полной training trajectory;
- equivalence для Adam или momentum SGD;
- equivalence reduced shortcut и iterative FixedPred;
- observer non-interference;
- runtime benefit.

## Evidence policy

Рабочие outputs сохраняются в игнорируемом каталоге `working/`.

После успешного confirmatory control создаётся отдельный immutable evidence package с manifest, bounded claim и SHA-256. Sealed EQ-S0 evidence не изменяется.

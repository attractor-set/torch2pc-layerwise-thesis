# Запечатывание evidence EQ-S2

## Статус

EQ-S2 прошёл confirmatory control в канонических Docker CPU и Docker/ROCm execution lanes.

## Сравнение

Reference:

- iterative FixedPred;
- `eta = 1`;
- `inference_steps = len(model) = 6`;
- feed-forward initialization.

Candidate:

- opt-in reduced shortcut;
- один joint state-and-parameter VJP на верхнеуровневый слой;
- `6` joint VJP calls;
- `6` detached graph islands;
- отсутствие `loss.backward()` в candidate;
- отсутствие iterative FixedPred loop в candidate.

## Объём проверки

- experiment source commit: `35527137e94b99fd74891739b982ad3181385256`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- seeds: `0, 1, 2`;
- batches на seed: `10`;
- runs на lane: `30`;
- endpoint-gradient comparisons: `300/300` на lane;
- parameter-after-step comparisons: `300/300` на lane;
- всего tensor comparisons: `1200/1200`.

## Поддерживаемое утверждение

При зарегистрированных lane-specific numerical thresholds iterative FixedPred с `eta = 1` и `inference_steps = len(model)` воспроизвёл endpoint gradients и параметры после одного шага stateless SGD относительно joint-VJP reduced shortcut на зарегистрированной выборке CPU и ROCm.

## Граница утверждения

EQ-S2 не устанавливает равенство промежуточных hidden-state trajectories, полной training trajectory, эквивалентность stateful optimizers, runtime или memory benefit, observer non-interference либо универсальную эквивалентность вне зарегистрированной архитектуры и среды.

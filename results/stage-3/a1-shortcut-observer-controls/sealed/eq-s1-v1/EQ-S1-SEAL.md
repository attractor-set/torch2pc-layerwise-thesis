# Запечатывание evidence EQ-S1

## Статус

EQ-S1 прошёл confirmatory control в канонических Docker CPU и Docker/ROCm execution lanes.

## Реализованный candidate

Reduced shortcut использует один joint state-and-parameter VJP на каждый верхнеуровневый слой.

Для `lenet_classic`:

- верхнеуровневых слоёв: `6`;
- joint VJP calls на run: `6`;
- graph islands: `6`;
- parameterized layers: `5`;
- parameter components: `10`;
- `loss.backward()` в candidate: не используется;
- iterative FixedPred loop: не используется.

## Объём проверки

- experiment source commit: `a2c634a066d871cf0dbf9c8e638dd830fe0e3705`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- seeds: `0, 1, 2`;
- batches на seed: `10`;
- runs на lane: `30`;
- endpoint-gradient comparisons: `300/300` на lane;
- parameter-after-step comparisons: `300/300` на lane;
- всего tensor comparisons: `1200/1200`.

## Поддерживаемое утверждение

При зарегистрированных lane-specific numerical thresholds reduced shortcut с одним joint VJP на слой воспроизвёл BP endpoint gradients и параметры после одного шага stateless SGD на зарегистрированной выборке CPU и ROCm.

## Граница утверждения

EQ-S1 не устанавливает эквивалентность hidden-state trajectories, полной training trajectory, stateful optimizers, runtime benefit или эквивалентность с iterative FixedPred. Последняя проверяется отдельно в EQ-S2.

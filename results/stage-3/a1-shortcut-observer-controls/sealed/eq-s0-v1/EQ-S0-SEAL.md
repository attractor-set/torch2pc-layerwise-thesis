# Запечатывание evidence EQ-S0

## Статус

EQ-S0 прошёл зарегистрированный расширенный контроль в канонических Docker CPU и Docker/ROCm execution lanes.

## Зарегистрированный объём

- source commit: `50d6e37183dec3e0719ad4a1f246d1b325d1b346`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- model seeds: `0, 1, 2`;
- batches на seed: `10`;
- runs на lane: `30`;
- endpoint-gradient comparisons: `300/300` на lane;
- parameter-after-step comparisons: `300/300` на lane;
- всего tensor comparisons: `1200/1200`;
- observer mode: `no_hooks`;
- optimizer: `SGD(lr=0.001, momentum=0.0)`.

## Числовые пороги

Использована зарегистрированная lane-specific threshold policy.

CPU:

- `min_cosine = 0.99999`;
- `max_relative_l2 = 1e-07`;
- `zero_atol = 1e-12`.

ROCm:

- `min_cosine = 0.999`;
- `max_relative_l2 = 0.001`;
- `zero_atol = 1e-07`.

CPU использует более строгие числовые допуски. Обе политики были зафиксированы в experiment source до выполнения контролей.

Model seed остаётся независимой экспериментальной единицей. Batches являются повторными контрольными наблюдениями внутри seed.

## Поддерживаемое утверждение

В зарегистрированной pinned-конфигурации и при зарегистрированных lane-specific порогах итеративный FixedPred при `eta=1` и `n=len(model)` воспроизвёл endpoint gradients BP и эквивалентные параметры после одного шага stateless SGD на проверенных seeds и batches в CPU и ROCm lanes.

## Граница утверждения

Этот gate не устанавливает эквивалентность промежуточных hidden-state trajectories, полной training trajectory, оптимизаторов с состоянием или reduced shortcut. EQ-S1, EQ-S2 и observer non-interference остаются открытыми gates.

## Происхождение

Полное происхождение, thresholds, environment metadata и агрегированные counts находятся в `eq_s0_evidence_manifest.json`. Целостность файлов проверяется через `SHA256SUMS`.

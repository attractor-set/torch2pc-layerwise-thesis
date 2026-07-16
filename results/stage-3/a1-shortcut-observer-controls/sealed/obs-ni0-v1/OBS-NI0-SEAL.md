# Запечатывание evidence OBS-NI0

## Статус

OBS-NI0 прошёл confirmatory control в канонических Docker CPU и Docker/ROCm execution lanes.

## Зарегистрированный observer

- schema: `stage3b-a1-obs-ni0-first-forward-io-v1`;
- capture policy: первый input и output каждого верхнеуровневого слоя;
- payload copy: `tensor.detach().clone()`;
- последующие forward calls учитываются без повторного захвата;
- все observer hooks удаляются до валидации.

## Сравниваемые arms

- iterative FixedPred без observer против того же FixedPred с passive observer;
- joint-VJP reduced shortcut без observer против того же shortcut с passive observer.

## Объём evidence

- preregistration commit: `9cb6399b4ad4b30397386a81af887e8b438c5251`;
- experiment source commit: `3cbda083bc5747732a51295da9a4494ffde48436`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- seeds: `0, 1, 2`;
- batches на seed: `10`;
- paired runs: `120`;
- endpoint-gradient comparisons: `1200`;
- parameter-after-step comparisons: `1200`;
- state records: `1080`;
- payload records: `1440`;
- failed и non-finite records: `0`.

## Поддерживаемое утверждение

В зарегистрированной CPU/ROCm выборке включение passive observer не изменило endpoint parameter gradients, параметры после одного stateless SGD step, optimizer state, model buffers, input и target tensors либо зарегистрированные RNG states для iterative FixedPred и joint-VJP reduced shortcut.

## Граница утверждения

OBS-NI0 не устанавливает неинтерферентность полной training trajectory или stateful optimizers, отсутствие runtime или memory overhead, механизмную валидность captured payload либо универсальность вне зарегистрированной архитектуры и среды.

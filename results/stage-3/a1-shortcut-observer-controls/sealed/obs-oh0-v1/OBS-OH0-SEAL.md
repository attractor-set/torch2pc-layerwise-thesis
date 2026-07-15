# Запечатывание evidence OBS-OH0

## Статус

OBS-OH0 прошёл confirmatory bounded-overhead control в канонических Docker CPU и Docker/ROCm lanes.

## Зарегистрированные объекты

- benchmark schema: `stage3b-a1-obs-oh0-v1`;
- observer schema: `stage3b-a1-obs-ni0-first-forward-io-v1`;
- preregistration commit: `9df364cbfbebb7293e78e1b4b26575aeab1171a1`;
- experiment source commit: `59dbcfa41a9c35cc8b72e75288aaa505459499d8`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

## Объём evidence

- correctness guards: `120`;
- measured timing pairs: `360`;
- timed executions: `720`;
- paired memory records: `120`;
- isolated memory workers: `240`;
- failed records: `0`;
- budget failures: `0`.

## Primary runtime ratios

- CPU FixedPred: `1.006993636`;
- CPU joint-VJP: `1.021382703`;
- ROCm FixedPred: `1.070112093`;
- ROCm joint-VJP: `1.137634067`.

Все четыре primary ratios находятся ниже зарегистрированного лимита `1.25`; все seed-level medians находятся ниже `1.35`.

## Retained payload

- CPU primary payload: `11,046,912` bytes;
- ROCm primary payload: `5,523,456` bytes;
- registered payload limit: `67,108,864` bytes.

CPU RSS и ROCm allocated-memory bounds выполнены для обоих arms и всех seeds.

## Инженерные замечания

Controlled runs вывели предупреждение PyTorch DataLoader: конфигурация запрашивала четыре worker process, тогда как CPU lane сообщал suggested maximum `1`. Dataloader и создание workers находились вне зарегистрированных measured timing и incremental-memory regions. Оба lanes завершились, correctness guards прошли, поэтому предупреждение не изменяет pass decision.

Предупреждение Tini относится к process reaping контейнера и не изменяет benchmark calculations или provenance.

## Поддерживаемое утверждение

Для iterative FixedPred и joint-VJP reduced shortcut зарегистрированный passive observer остался внутри preregistered runtime и retained-memory budgets в controlled CPU/ROCm confirmatory sample.

## Граница утверждения

OBS-OH0 не устанавливает нулевой overhead, full-training overhead, overhead stateful optimizers, применимость к другим models и batch sizes, механизмную валидность payload или causal validity PC-CATM.

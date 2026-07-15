# OBS-OH0 evidence seal

## Status

OBS-OH0 passed the confirmatory bounded-overhead control in the canonical Docker CPU and Docker/ROCm lanes.

## Registered objects

- benchmark schema: `stage3b-a1-obs-oh0-v1`;
- observer schema: `stage3b-a1-obs-ni0-first-forward-io-v1`;
- preregistration commit: `9df364cbfbebb7293e78e1b4b26575aeab1171a1`;
- experiment source commit: `59dbcfa41a9c35cc8b72e75288aaa505459499d8`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

## Evidence volume

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

All four primary ratios are below the registered `1.25` limit, and every seed-level median is below `1.35`.

## Retained payload

- CPU primary payload: `11,046,912` bytes;
- ROCm primary payload: `5,523,456` bytes;
- registered payload limit: `67,108,864` bytes.

The CPU RSS and ROCm allocated-memory bounds passed for both arms and every seed.

## Engineering notes

The controlled runs emitted a PyTorch DataLoader warning because the configuration requested four worker processes while the CPU lane reported a suggested maximum of `1`. Data loading and worker creation were outside the registered measured timing and incremental-memory regions. Both lanes completed and all correctness guards passed, so the warning does not change the pass decision.

The Tini warning concerns container process reaping and does not alter benchmark calculations or provenance.

## Supported claim

For iterative FixedPred and the joint-VJP reduced shortcut, the registered passive observer remained within the preregistered runtime and retained-memory budgets in the controlled CPU/ROCm confirmatory sample.

## Claim boundary

OBS-OH0 does not establish zero overhead, full-training overhead, overhead for stateful optimizers, applicability to other models and batch sizes, mechanistic validity of payload, or causal validity of PC-CATM.

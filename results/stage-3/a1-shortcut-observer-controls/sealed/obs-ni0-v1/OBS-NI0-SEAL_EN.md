# OBS-NI0 evidence seal

## Status

OBS-NI0 passed the confirmatory control in the canonical Docker CPU and Docker/ROCm execution lanes.

## Registered observer

- schema: `stage3b-a1-obs-ni0-first-forward-io-v1`;
- capture policy: the first input and output of every top-level layer;
- payload copy: `tensor.detach().clone()`;
- later forward calls are counted without additional capture;
- all observer hooks are removed before validation.

## Compared arms

- iterative FixedPred without the observer versus the same FixedPred path with the passive observer;
- the joint-VJP reduced shortcut without the observer versus the same shortcut with the passive observer.

## Evidence volume

- preregistration commit: `9cb6399b4ad4b30397386a81af887e8b438c5251`;
- experiment source commit: `3cbda083bc5747732a51295da9a4494ffde48436`;
- Torch2PC commit: `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- seeds: `0, 1, 2`;
- batches per seed: `10`;
- paired runs: `120`;
- endpoint-gradient comparisons: `1200`;
- parameter-after-step comparisons: `1200`;
- state records: `1080`;
- payload records: `1440`;
- failed and non-finite records: `0`.

## Supported claim

In the registered CPU/ROCm sample, enabling the passive observer did not change endpoint parameter gradients, parameters after one stateless SGD step, optimizer state, model buffers, input or target tensors, or registered RNG states for iterative FixedPred and the joint-VJP reduced shortcut.

## Claim boundary

OBS-NI0 does not establish non-interference over a full training trajectory or for stateful optimizers, absence of runtime or memory overhead, mechanistic validity of captured payload, or universality outside the registered architecture and environment.

# ADR-116: attempt-003 host invocation chain authoring

## Status

Accepted as bounded authoring of the future host invocation chain. No host
command is executed or persisted by this slice.

## Context

PR #185 merged the exact authorization [evidence](../glossary_EN.md#term-evidence) for [attempt](../glossary_EN.md#term-attempt) 003 into `main` as
`e7a0fb92d17bdb9a1165f211db7a1e94ff296999`. The authorization has canonical
identity
`sha256:46baed5cebc1efe4abf68c21652775eee5c1123df09465d332c151303d890d63`,
is effective and unconsumed, and is bound to the [execution](../glossary_EN.md#term-execution) freeze
`sha256:82e7509a0d2627f8b91daa34049307da573619b740a2022b72b922edcd07898e`.
The local frozen image, pinned Torch2PC checkout, and ROCm devices have been
observed as ready, but the preflight correctly rejected [runtime](../glossary_EN.md#term-runtime) invocation
because no Attempt-003 host invocation chain exists.

The historical implementation and source-binding records intentionally remain
unchanged with `host_invocation_chain_authored=false`. They are evidence of the
state in which those earlier slices were authored and must not be rewritten.

The runtime entrypoint is already irreversible at the lease boundary: after it
verifies the freeze and authorization it materializes the execution lease before
calling the runtime backend. Therefore a host command cannot be improvised at
execution time. Its image, mounts, environment, devices, resources and security
policy must be a separate exact contract.

## Decision

Add a pure Attempt-003 host invocation-chain module, frozen authoring package,
verifier and focused tests. The contract is bound to:

- merged authorization parent `e7a0fb92d17bdb9a1165f211db7a1e94ff296999`;
- runtime source commit `541b34a57297d2c5a82851bd846b583d4904fba6`;
- Torch2PC `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- frozen image
  `torch2pc-layerwise-thesis@sha256:aec2178f1de409143553ccaecb34b2d0e4d19332040fce56742e422f770ef188`;
- pinned ROCm/PyTorch base image;
- exact Attempt-003 output, lease and durable-outcome paths.

The future Docker command may be constructed only as data. It uses exactly
three bind mounts:

1. `experiments/frozen` -> `/workspace/experiments/frozen`, read-only;
2. `external/Torch2PC` -> `/workspace/external/Torch2PC`, read-only;
3. `results` -> `/workspace/results`, read-write.

The project source tree and [dataset](../glossary_EN.md#term-dataset) are not mounted. The container uses the
exact repository digest already frozen in the execution freeze, disabled
networking, read-only root filesystem, no new privileges, all capabilities
dropped, automatic removal, fixed working directory, exact GPU device
bindings, explicit UID/GID and resource limits, and a fixed environment plus
explicit thread/GPU bindings. Shell interpretation and inherited environment
are forbidden.

The module may parse previously captured `docker image inspect` JSON and may
construct the exact `docker run` argv in memory. It contains no process
spawner. Construction requires the exact lease acknowledgement
`CLAIM_QWAKE_LC4_ATTEMPT_003_FROM_CORRECTED_EXECUTION_FREEZE`.

## Historical-state rule

This ADR does not rewrite the older implementation or source-binding records.
Their `host_invocation_chain_authored=false` values remain true statements
about those historical authoring moments. The new host-chain package is a later
layer that proves the transition to an authored host contract.

## Boundary

This slice does not consume authorization, create a lease or outcome, persist a
host command, build or run Docker, spawn a process, invoke runtime or model
code, access a dataset, or publish evidence.

`runtime_execution_permitted=false` remains part of the host contract. After
this slice is merged and independently verified, a separate non-executing host
command materialization/prelaunch verification step is required before any
one-shot runtime invocation can become admissible.

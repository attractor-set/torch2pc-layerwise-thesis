# ADR-114: pure attempt-002 host invocation chain

- **Status:** accepted within the sole corrective PR #179
- **Date:** 2026-08-04
- **Related decisions:** [ADR-111](ADR-111-stage3b-qwake-lc4-e-claim-execute-order-correction_EN.md), [ADR-112](ADR-112-stage3b-qwake-lc4-e-attempt-002-container-runtime_EN.md), [ADR-113](ADR-113-stage3b-qwake-lc4-e-attempt-002-execution-freeze_EN.md)

## Context

ADR-113 froze the corrected image, its local identity, and the distinct [attempt](../glossary_EN.md#term-attempt)-002 [freeze](../glossary_EN.md#term-freeze). Before a new one-shot authorization can be authored, the host side must be shown to no longer depend on the image, effect paths, or command chain of terminal attempt 001.

The historical ADR-072 through ADR-085 modules are bound to the former image and former effect paths. Reusing them for attempt 002 is forbidden. The replacement chain must be separate, verifiable, and non-executing.

## Decision

Add a pure attempt-002 host invocation chain. It:

- reverifies the ADR-113 package without requiring future in-container environment variables;
- loads the exact normalized corrected-image identity;
- accepts `docker image inspect` output only as input data and never invokes Docker itself;
- requires the exact repository digest `torch2pc-layerwise-thesis@sha256:f78fdbc699f3d00347d1dfdb78c03dd3df3957371f64eca9488de7cc06ce2b1d`;
- permits exactly three mounts: read-only `experiments/frozen`, read-only `external/Torch2PC`, and read-write `results`;
- forbids project-source and [dataset](../glossary_EN.md#term-dataset) mounts;
- fixes disabled networking, a read-only root filesystem, no added privileges, automatic container removal, and exact GPU devices;
- validates canonical UID, GID, CPU, memory, shared-memory, temporary-filesystem, and thread-count inputs;
- constructs the exact future command argv as immutable data;
- contains no process spawner, `subprocess`, automatic retry, or durable command writer.

The future command addresses the attempt-002 container entrypoint:

```text
/workspace/scripts/run_stage3b_qwake_lc4_attempt_002_authorized_runtime.py
```

It can carry the exact timestamp and lease acknowledgement only after a separate future one-shot authorization has been verified. A pure command constructor is not authority to apply the command.

## Current-slice boundary

```text
ATTEMPT_002_EXECUTION_FREEZE_VERIFIED=true
HOST_IMAGE_IDENTITY_PRESENT=true
HOST_INVOCATION_CONTRACT_PRESENT=true
HOST_COMMAND_MATERIALIZATION_PRESENT=true
HOST_PROCESS_SPAWNER_PRESENT=false
DOCKER_RUN_IMPLEMENTED=false
DOCKER_BUILD_INVOKED=false
DOCKER_RUN_INVOKED=false
CONTAINER_CREATED=false
ATTEMPT_002_AUTHORIZATION_AUTHORING_ADMISSIBLE=true
ATTEMPT_002_AUTHORIZATION_ISSUED=false
ATTEMPT_002_AUTHORIZATION_CONSUMED=false
ATTEMPT_002_LEASE_V1_PRESENT=false
ATTEMPT_002_LEASE_V2_PRESENT=false
ATTEMPT_002_DURABLE_OUTCOME_PRESENT=false
ATTEMPT_002_RUNTIME_STARTED=false
ATTEMPT_002_RUNTIME_PERFORMED=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
QW5_OPENED=false
```

## Verifiable invariants

1. Every image identity equals ADR-113.
2. The command vector uses only the exact image repository digest.
3. Shell interpretation and environment inheritance are forbidden.
4. Neither the project source tree nor a dataset is mounted.
5. Existing authorization or any attempt-002 effect closes the authoring surface.
6. The module cannot create a process or container.
7. Terminal attempt-001 objects are neither included nor modified.

## Consequences

After independent verification of this commit, authoring a distinct attempt-002 one-shot authorization becomes admissible. Authorization, consumption, container invocation, lease creation, durable outcome, and [execution](../glossary_EN.md#term-execution) remain separate future transitions. PR #179 must not yet be merged.

# ADR-115: one-shot attempt-002 host-invocation authorization

- **Status:** accepted within the sole corrective PR #179
- **Date:** 2026-08-04
- **Related decisions:** [ADR-111](ADR-111-stage3b-qwake-lc4-e-claim-execute-order-correction_EN.md), [ADR-112](ADR-112-stage3b-qwake-lc4-e-attempt-002-container-runtime_EN.md), [ADR-113](ADR-113-stage3b-qwake-lc4-e-attempt-002-execution-freeze_EN.md), [ADR-114](ADR-114-stage3b-qwake-lc4-e-attempt-002-host-invocation-chain_EN.md)

## Context

The fourth PR #179 commit independently verified the corrected image, the distinct [freeze](../glossary_EN.md#term-freeze) for [attempt](../glossary_EN.md#term-attempt) 002, and the pure future host invocation chain. The next admissible transition is a distinct one-shot authorization. It must not create a process, container, lease, durable outcome, or start [execution](../glossary_EN.md#term-execution).

The authorization must be bound to the exact ADR-113 and ADR-114 identities and cannot grant scientific execution, [dataset](../glossary_EN.md#term-dataset) access, or publication authority.

## Decision

Create canonical object `stage3b-qwake-lc4-e-attempt-002-authorization-v1`. It:

- is bound to attempt `stage3b-qwake-lc4-runtime-validation-v1-attempt-002`;
- is bound to `freeze_sha256=sha256:09ca6e2b70fe1c7352c35d694952b4ea199e85dd816588f29454a4157b711f5c`;
- is bound to local operator `dzmitry-prychyna`;
- requires exact phrase `AUTHORIZE_QWAKE_LC4_ATTEMPT_002_ONE_SHOT_ENGINEERING_INVOCATION`;
- admits exactly one engineering application;
- forbids automatic and blind retry;
- remains unconsumed and does not start the attempt;
- does not open scientific execution, [test-dataset access](../glossary_EN.md#term-test-dataset-access), or publication.

The current computed host-chain state moves from `authorization_absent` to `authorized_unconsumed`. The historical ADR-114 package is not semantically rewritten: its authoring record continues to prove the pre-authorization state, while the updated verifier separately proves the current post-authorization state.

## Current-slice boundary

```text
ATTEMPT_002_AUTHORIZATION_EFFECTIVE=true
ATTEMPT_002_AUTHORIZATION_ISSUED=true
ATTEMPT_002_AUTHORIZATION_CONSUMED=false
ATTEMPT_002_ATTEMPT_STARTED=false
AUTHORIZATION_CONSUMPTION_PERMITTED=false
POST_COMMIT_VERIFICATION_REQUIRED_BEFORE_CONSUMPTION=true
HOST_PROCESS_SPAWNER_PRESENT=false
DOCKER_RUN_IMPLEMENTED=false
DOCKER_BUILD_INVOKED=false
DOCKER_RUN_INVOKED=false
CONTAINER_CREATED=false
ATTEMPT_002_LEASE_V1_PRESENT=false
ATTEMPT_002_LEASE_V2_PRESENT=false
ATTEMPT_002_DURABLE_OUTCOME_PRESENT=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
PR_MERGED=false
QW5_OPENED=false
```

## Verifiable invariants

1. The authorization object is canonical JSON with its own SHA-256.
2. Authorization is bound to the exact freeze, image, and host-invocation identities.
3. `execution_count` is `1` and retry is forbidden.
4. Authorization exists but is unconsumed; neither the attempt nor [runtime](../glossary_EN.md#term-runtime) has started.
5. Attempt-002 result, lease, and durable-outcome paths are absent.
6. Authoring and verification modules contain no process-spawning surface.
7. Terminal attempt-001 [evidence](../glossary_EN.md#term-evidence) objects remain byte exact.

## Consequences

After independent verification of the fifth commit, a distinct one-shot host operation may be authored to atomically consume the authorization and invoke the already frozen command chain. That future transition is outside ADR-115. PR #179 must not yet be merged; [run](../glossary_EN.md#term-run) and QW-5 remain closed.

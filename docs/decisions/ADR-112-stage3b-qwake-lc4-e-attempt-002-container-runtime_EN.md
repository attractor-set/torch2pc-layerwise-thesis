# ADR-112: isolated attempt-002 container runtime

- **Status:** accepted inside the sole corrective PR #179
- **Date:** 2026-08-04
- **Related decision:** [ADR-111](ADR-111-stage3b-qwake-lc4-e-claim-execute-order-correction_EN.md)

## Context

Terminal [attempt](../glossary_EN.md#term-attempt) 001 ended with a nonzero return code after lease v1 was created. Retry of that attempt is forbidden. ADR-111 corrected the verify-and-claim ordering defect, but its initial corrected entry point still referenced attempt-001 paths and the historical image freeze. That object cannot govern a distinct attempt.

## Decision

Introduce a versioned container [runtime](../glossary_EN.md#term-runtime) dedicated to attempt 002. It defines independent output, lease-v1, future lease-v2, and durable host-outcome paths. One admission object is carried through lease construction, atomic materialization, and claimed-wrapper [execution](../glossary_EN.md#term-execution).

The new runtime:

- imports no historical admission, authorization-consumption, or persistent-chain module for attempt 001;
- owns distinct image-freeze, authorization, admission, lease, and receipt structures;
- reuses only the immutable synthetic engineering-matrix executor;
- creates lease v1 without replacement and with mode `0600`;
- uses a temporary tree and atomic no-replace output promotion;
- rejects reuse after either lease or output exists;
- accesses no scientific [dataset](../glossary_EN.md#term-dataset) and opens no publication capability.

## Current-slice boundary

This slice authors code and a verifiable package only. It does not materialize the corrected image freeze, issue attempt-002 authorization, create a lease, build an image, or invoke runtime execution.

```text
ATTEMPT_002_CONTAINER_RUNTIME_AUTHORED=true
CORRECTED_IMAGE_BUILT=false
ATTEMPT_002_EXECUTION_FREEZE_MATERIALIZED=false
ATTEMPT_002_AUTHORIZATION_ISSUED=false
ATTEMPT_002_LEASE_V1_PRESENT=false
ATTEMPT_002_LEASE_V2_PRESENT=false
ATTEMPT_002_DURABLE_OUTCOME_PRESENT=false
ATTEMPT_002_RUNTIME_STARTED=false
ATTEMPT_002_RUNTIME_PERFORMED=false
QW5_OPENED=false
```

## Consequences

After this commit is added to PR #179 and independently verified, the next admissible action is to build the corrected image from the exact PR head. Image identity, execution freeze, one-shot authorization, and the host invocation chain must then be materialized separately. Runtime invocation remains forbidden until those records are complete.

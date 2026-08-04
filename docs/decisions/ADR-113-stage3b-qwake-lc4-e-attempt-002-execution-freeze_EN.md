# ADR-113: corrected image and attempt-002 execution freeze

- **Status:** accepted within the sole corrective PR #179
- **Date:** 2026-08-04
- **Related decisions:** [ADR-111](ADR-111-stage3b-qwake-lc4-e-claim-execute-order-correction_EN.md), [ADR-112](ADR-112-stage3b-qwake-lc4-e-attempt-002-container-runtime_EN.md)

## Context

After independent verification of the second PR #179 commit, one corrected container image was built for [attempt](../glossary_EN.md#term-attempt) 002 from exact commit `02afcc3e79b2d456cc3f1c075d4d792a0be608f7`. The build context came from `git archive`, so the durable objects of terminal attempt 001 were not included in the image. The image was inspected twice without container creation and without a [run](../glossary_EN.md#term-run).

## Decision

A distinct attempt-002 [execution](../glossary_EN.md#term-execution) [freeze](../glossary_EN.md#term-freeze) is materialized. It binds:

- the exact source commit and pinned Torch2PC commit;
- the attempt-002 contract, wrapper, backend, and container entrypoint identities;
- corrected image `sha256:f78fdbc699f3d00347d1dfdb78c03dd3df3957371f64eca9488de7cc06ce2b1d`;
- the local repository digest with the same SHA-256;
- the pinned ROCm base image;
- preserved external build capture `sha256:2aa105d8c13ef2408e674c08d7210c318a4baebf090b351ceb80ea1cf3de3902`;
- the existing scientific authorization only as the immutable source of the permitted engineering matrix;
- the disjoint output, lease, and durable-outcome paths of attempt 002.

The repository retains a normalized image identity and a reference to the external capture directory without a user-specific absolute path. The large source archive, build log, and complete Docker responses remain in the preserved external directory.

## Current-slice boundary

This slice does not issue the attempt-002 one-shot authorization and does not prepare the host invocation command. The image exists locally, but no container was created.

```text
CORRECTED_IMAGE_BUILT=true
CORRECTED_IMAGE_INSPECTION_COUNT=2
CORRECTED_IMAGE_CONTAINER_CREATED=false
ATTEMPT_002_EXECUTION_FREEZE_MATERIALIZED=true
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

## Consequences

The next admissible slice must first author and independently verify a corrected host invocation chain bound to the new digest and attempt-002 paths. A separate one-shot authorization may be authored only after that verification. PR #179 merge and [execution](../glossary_EN.md#term-execution) remain forbidden.

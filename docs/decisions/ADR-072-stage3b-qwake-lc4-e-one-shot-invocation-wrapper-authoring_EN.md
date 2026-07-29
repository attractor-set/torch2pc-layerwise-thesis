# ADR-072: QW-LC4-E one-shot host invocation-wrapper authoring

[Russian version](ADR-072-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-authoring.md)

- **Status:** accepted as an authoring slice; no host invoker exists
- **Date:** 29 July 2026
- **Slice:** `QW-LC4-E-one-shot-invocation-wrapper-authoring`

## Context

Authorization for one future engineering invocation merged through PR #132
into `main` as `8337d9ad0ac21a69a577ab74a73d05d69f8fa7a1` and passed independent
verification. It permits a future lease claim and invocation of the exact
immutable image while retaining the branch gate
`branch_runtime_execution_permitted=false`.

The image already contains an entrypoint that, when explicitly invoked,
verifies `execution-freeze-v1`, claims the lease, and executes the synthetic
matrix. The host layer therefore must not be combined with [execution](../glossary_EN.md#term-execution). Its
mount, environment, image-verification, and isolation contract is authored
first as an effect-free slice.

## Decision

1. Add the pure `stage3b_qwake_lc4_invocation_wrapper.py` module. It reverifies
   the exact authorization package and constructs only a canonical future
   invocation contract.
2. Bind the contract to the PR #132 merge/head, authorization SHA-256, exact
   image repo digest, image source commit, Torch2PC, and the in-image entrypoint.
3. Permit exactly three future bind mounts:
   - read-only `experiments/frozen -> /workspace/experiments/frozen`;
   - read-only `external/Torch2PC -> /workspace/external/Torch2PC`;
   - read-write `results -> /workspace/results`.
4. Forbid binding the project source tree or any [dataset](../glossary_EN.md#term-dataset).
5. Require a future implementation to address the image by repo digest, verify
   its digest and source-revision label before invocation, disable networking,
   use a read-only root filesystem, enable `no-new-privileges`, drop all
   capabilities, and prohibit privileged mode.
6. Require a dedicated `/tmp` tmpfs because the frozen image entrypoint creates
   `/tmp/home`; its size is an explicit `TMPFS_SIZE` input.
7. Freeze future `/dev/kfd` and `/dev/dri` attachments, `HOST_UID:HOST_GID`,
   supplementary `VIDEO_GID` and `RENDER_GID`, CPU affinity, memory, shared
   memory, and thread-limit inputs.
8. Freeze the exact in-image command template with `{CLAIMED_AT_UTC}` as its
   only dynamic value. Host resource values must be validated before command
   materialization; this slice reads none of them.
9. Claim and execution remain one process, and retry after claim remains
   forbidden.
10. The verifier may only construct, serialize under a temporary directory, and
   reload the contract. It imports no tensor [runtime](../glossary_EN.md#term-runtime), invokes no container
   runtime, and creates no repository effect.

## Machine-readable contract

```text
contract_id=stage3b-qwake-lc4-e-one-shot-host-invocation-wrapper-contract-v1
contract_sha256=sha256:4c4cb163e8c2a33b0563cc3b9cb873a87acf8ea75bb3e807d157d51c5a4dd29b
authorization_merge_commit=8337d9ad0ac21a69a577ab74a73d05d69f8fa7a1
authorization_head_commit=ca6363c11218575d567c5dd6cbe8818d10a86d41
image_repo_digest=torch2pc-layerwise-thesis@sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d
```

## Boundaries

```text
INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
INVOCATION_WRAPPER_AUTHORING_BRANCH_OPEN=true
INVOCATION_WRAPPER_CONTRACT_PRESENT=true
CONTAINER_COMMAND_TEMPLATE_PRESENT=true
GPU_DEVICE_BINDING_COUNT=2
TMPFS_REQUIRED=true
TMPFS_TARGET=/tmp
HOST_RUNTIME_INVOKER_PRESENT=false
IMAGE_INSPECTION_IMPLEMENTED=false
INVOCATION_COMMAND_MATERIALIZED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

After commit, merge, and independent verification, a separate slice may
implement the host invoker. Code availability still must not open execution.
The actual one-shot command is admissible only after a separate verification of
the exact implementation commit, local image identity, and every resource
input.

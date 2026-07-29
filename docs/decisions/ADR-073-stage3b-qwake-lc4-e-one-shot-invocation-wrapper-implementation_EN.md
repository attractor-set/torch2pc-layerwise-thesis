# ADR-073: QW-LC4-E one-shot host invocation-wrapper implementation

[Russian version](ADR-073-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-implementation.md)

- **Status:** accepted as an implementation with no host [runtime](../glossary_EN.md#term-runtime) invoker
- **Date:** 29 July 2026
- **Slice:** `QW-LC4-E-one-shot-invocation-wrapper-implementation`

## Context

PR #133 containing the pure wrapper contract merged into `main`
`7cc17c6b36cb5115e63a2b64e4bff90a525b2465` and passed independent
verification. The contract requires exact local-image inspection and canonical
command construction before a future invocation, while keeping
[execution](../glossary_EN.md#term-execution) forbidden on the implementation
branch.

The local image is frozen as
`torch2pc-layerwise-thesis@sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d`.
Its normalized inspection record belongs to the immutable
`execution-freeze-v1` package. The implementation must therefore compare the
current Docker observation with that record instead of trusting a tag or an
operator-provided image string.

## Decision

1. Add the separate
   `stage3b_qwake_lc4_invocation_wrapper_implementation.py` module.
2. Permit exactly one observational external operation: `docker image inspect`
   for the exact image repo digest.
3. Forbid a shell, `docker pull`, container execution, tensor
   [runtime](../glossary_EN.md#term-runtime) imports, lease claims, and result
   writes.
4. Normalize and compare the current image against the frozen record across:
   - image ID and `RepoDigests`;
   - mandatory tag membership;
   - [architecture](../glossary_EN.md#term-architecture), OS, creation time, size, and every `RootFS` layer;
   - `org.opencontainers.image.revision` and `io.torch2pc.base-image` labels;
   - in-image `SOURCE_GIT_COMMIT`;
   - exact image entrypoint and working directory.
5. Accept exactly 13 host-resource inputs. IDs, GPU list, CPU set, sizes,
   and thread counts must be canonical; missing, extra, or ambiguous values
   fail closed.
6. Materialize the future `docker run` command only as an immutable in-memory
   argv tuple. It must include `--pull=never`, disabled networking, a read-only
   root filesystem, `no-new-privileges`, all-capability drop, two devices, and
   exactly the three mounts frozen by ADR-072.
7. Persist no command and expose no function that can execute it. The sole
   `subprocess.run` call belongs to image inspection.
8. Preserve the lease, authorization, [evidence](../glossary_EN.md#term-evidence),
   [dataset](../glossary_EN.md#term-dataset), and publication boundaries.

## Machine-readable boundary

```text
implementation_id=stage3b-qwake-lc4-e-one-shot-host-invocation-wrapper-implementation-v1
implementation_base_commit=7cc17c6b36cb5115e63a2b64e4bff90a525b2465
wrapper_contract_sha256=sha256:4c4cb163e8c2a33b0563cc3b9cb873a87acf8ea75bb3e807d157d51c5a4dd29b
frozen_image_inspection_sha256=sha256:d771d93b4b3c38599fee9fbf90971bc8d00d9cd7da4cbe90cef67c84d761d675
```

```text
IMAGE_INSPECTION_IMPLEMENTED=true
INVOCATION_COMMAND_MATERIALIZED=true
INVOCATION_COMMAND_PERSISTED=false
HOST_RUNTIME_INVOKER_PRESENT=false
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

After merge and independent verification, the repository will contain exact
image inspection and deterministic command construction. Their availability
does not open [execution](../glossary_EN.md#term-execution). An actual invocation
still requires a separate implementation freeze, validation of real host
inputs, and a separate atomic step that consumes the one-shot authorization,
claims the lease, and invokes the frozen entrypoint without retry.

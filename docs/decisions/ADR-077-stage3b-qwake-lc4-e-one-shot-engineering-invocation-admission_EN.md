# ADR-077: one-shot engineering invocation admission for `QW-LC4-E`

[Russian version](ADR-077-stage3b-qwake-lc4-e-one-shot-engineering-invocation-admission.md)

- **Status:** accepted as admission authoring; [execution](../glossary_EN.md#term-execution) has not started
- **Date:** 29 July 2026
- **Base commit:** `3454d12d3cc16c9c50977e2a598e2bc1a8768441`

## Context

PR #137 completed the host [runtime](../glossary_EN.md#term-runtime)-invoker repository freeze. A one-shot future
authorization already exists, and the invoker can execute the exact `docker run`.
Those capabilities do not permit immediate execution. A separate operator
operation must first bind the exact merge, immutable authorization, invoker
implementation, image, Torch2PC revision, and absent lease/output state.

## Decision

Materialize the two-file
`stage3b-qwake-lc4-e-one-shot-engineering-invocation-admission-v1` package, a
pure verification module, a CLI verifier, and negative tests. The admission:

1. binds the PR #137 merge commit and both parents;
2. reverifies the exact one-shot authorization package;
3. reverifies the host invoker semantic state and frozen package;
4. requires future double local-image inspection, host-resource validation,
   and absence of lease, output, and staging in the operator operation;
5. preserves `preexecution_identity_verified=false` because runtime state has
   not yet been inspected;
6. keeps branch permission and every runtime effect closed.

The verifier does not import the invocation function, inspect an image,
materialize the command, or create a child process.

## Identities

```text
invocation_base_commit=3454d12d3cc16c9c50977e2a598e2bc1a8768441
repository_freeze_head=cc287334a325f460555bab06725c52ba548985eb
repository_freeze_parent=da51c8d858c541372525125640db99062041fc20
invocation_authorization_sha256=sha256:0a60dacc1bfd5073cf52d76f2ec33ae54f00899aad9877d44607199659fda75a
host_runtime_invoker_implementation_sha256=sha256:1f5f31d4f220bbf074736f1de0b78a5dafa2849188ac337704d5cc704668fdf4
host_runtime_invoker_contract_sha256=sha256:607bf719d8a976569c50d7cfe8604ab341843dad00d3eef8784e1dc6cfd9b88d
image_repo_digest=torch2pc-layerwise-thesis@sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d
admission_sha256=sha256:fe07bc20bf5866d84730df945c2ababc7b5f4f255648c5de6e3185ba4e37c01d
admission_file_sha256=sha256:319f415265d041d883c3980f884dcb736f6f236a90ed3777c65e1ae10b7c9bba
package_registry_sha256=sha256:bc4bacb646759e8fa42caf336229a647e7a6d87a9ba292faf38ca9055b3b6ac2
module_sha256=sha256:53264f77a5e72fa4933f0a68825c07dcde01b7e2d362de0cba1b4394113c436f
verifier_sha256=sha256:06f61646988f7798cc57a47796fe0d5f4fff12f3d2fe4c5536b8f64617cd2148
test_sha256=sha256:ff9841329831bbfe84fb0fa571ef5f1a6ab6209b97a4e20f51a1ee68bd4f5b3f
```

## Boundary

```text
REPOSITORY_FREEZE_COMPLETE=true
INVOCATION_ADMISSION_RECORD_PRESENT=true
PREEXECUTION_IDENTITY_CHECKS_IMPLEMENTED=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

A separate slice must merge and independently verify this admission. Only then
may an operator operation revalidate runtime state and either perform exactly
one invocation or fail closed.

# ADR-080: pre-execution verification contract for the `QW-LC4-E` one-shot engineering invocation

[Русская версия](ADR-080-stage3b-qwake-lc4-e-one-shot-engineering-invocation-preexecution-verification.md)

- **Status:** accepted as contract authoring; dynamic verification and [execution](../glossary_EN.md#term-execution) have not started
- **Date:** 29 July 2026
- **Base commit:** `49c4b97e93b47cefbf35576736927ece02c9402b`

## Context

PR #140 merged the authorization for one future engineering invocation. That
authorization requires current image, host-resource, canonical argv, and closed
effect-boundary verification to occur in the same process that subsequently
creates the single child process. A separate preparatory check cannot count as
current-[runtime](../glossary_EN.md#term-runtime) verification: it would break check-to-spawn continuity and
increase the contracted image-inspection and command-materialization counts.

Before the actual [run](../glossary_EN.md#term-run), the repository therefore
needs an exact contract for that continuity and a fail-closed verifier that
proves the already implemented host invoker is unchanged without calling it.

## Decision

Materialize the two-file package
`stage3b-qwake-lc4-e-one-shot-engineering-invocation-preexecution-verification-v1`,
a pure module, a command-line verifier, and negative tests. The contract:

1. binds the PR #140 merge commit, authorization head, parent, and complete
   `execution-authorization-v1` package;
2. rebinds the exact host-invoker contract and implementation, immutable image,
   Torch2PC revision, output root, and lease path;
3. requires one direct future call to `invoke_one_shot_host_runtime` from the
   atomic runtime operation, with no separate dynamic verification in between;
4. fixes the 13 host-resource keys, two image inspections, two canonical argv
   materializations, equality of both pairs, and at most one shell-free
   `Popen`;
5. requires unconsumed authorization and absent lease, output, and staging
   immediately before child creation;
6. forbids command or host-log persistence, host lease writes, and automatic
   retry after child creation;
7. verifies only the static contract and preserves
   `PREEXECUTION_IDENTITY_VERIFIED=false` until the future current-runtime call.

The verifier calls only pure checks for frozen packages and implementation
state. It does not execute `docker image inspect`, materialize an invocation
command, call `Popen`, create a lease, or produce [evidence](../glossary_EN.md#term-evidence).

## Identities

```text
preexecution_base_commit=49c4b97e93b47cefbf35576736927ece02c9402b
authorization_head_commit=9b7074cbb602fff77ad6770ea4978d3bdc73003b
authorization_parent_commit=b0f6729e8fd1cb1aa172eef488dc56e36b335173
authorization_merged_at_utc=2026-07-29T21:46:26Z
execution_authorization_sha256=sha256:ff136538faee0d7952dc444e521d7ec760c7d54cd38406cb9b19ff1e00d9437b
preexecution_verification_sha256=sha256:833371b427a5c8a6e602d675711b85b2edc68441b9e5be191321a2911bce6128
verification_file_sha256=sha256:a0f19309fc7bb2abe47f300a793423e8c764d6330220b4d4e8db3724c01df9f1
package_registry_sha256=sha256:cee3dda10e7d1249ae0a6fb56173a491dd2b87adb916b42b88a10e9e9c801028
module_sha256=sha256:cae8721fb3278a3fbfeda8db366e864b75dd576fae90cfafe4c62301205dd2f6
verifier_sha256=sha256:bf052424ecfabe85741ce4ddf13112db5797c2bc666c6b026bb4dd9bac55e4cd
test_sha256=sha256:18386e940984402b5e54c66c9a93cbf692a73be8e2ee4ee6c858a9a314cd1752
```

## Boundaries

```text
INVOCATION_OPERATION_COMPLETE=true
EXECUTION_AUTHORIZATION_COMPLETE=true
PREEXECUTION_VERIFICATION_RECORD_PRESENT=true
PREEXECUTION_VERIFIER_IMPLEMENTED=true
PREEXECUTION_STATIC_CONTRACT_VERIFIED=true
PREEXECUTION_VERIFICATION_SLICE_OPEN=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_EXECUTION_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_OPEN=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

After this contract is committed and merged, only the separate atomic runtime
operation may be opened. It must call the exact host invoker once; both image
inspections and both command materializations must occur in that same process
immediately before the single child creation. Any mismatch fails closed and
permits neither a bypass nor an automatic retry.

# ADR-081: bounded `QW-LC4-E` one-shot engineering invocation runtime operation

[Русская версия](ADR-081-stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation.md)

- **Status:** accepted as operation authoring; dynamic verification and [execution](../glossary_EN.md#term-execution) have not started
- **Date:** 29 July 2026
- **Base commit:** `494e6a0b2f10c26b49c90fbb84c23565699a4064`

## Context

PR #141 merged the static pre-execution verification contract. The next slice
must define the single entry point that, after separate merge verification, can
delegate one call to the already frozen host invoker. The new entry point must
not duplicate image inspection, command materialization, or child creation:
those actions are already joined inside `invoke_one_shot_host_runtime` and must
remain in one continuous process.

The presence of an executable function is not execution permission. The
authoring branch must preserve an explicitly closed permission, an empty effect
boundary, and `PREEXECUTION_IDENTITY_VERIFIED=false`.

## Decision

Materialize the two-file package
`stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation-v1`, a
pure machine-readable contract, a verifier, negative tests, and the bounded
entry point `execute_one_shot_engineering_invocation_runtime_operation`.

The contract:

1. binds the PR #141 merge commit, pre-execution head and parent, and the full
   `preexecution-verification-v1` package;
2. rebinds the exact host invoker, one-shot authorization, immutable image,
   Torch2PC revision, output root, and lease path;
3. requires a separate exact operation acknowledgement and literal
   `runtime_execution_permitted=true`;
4. requires a UTC claim time after the PR #141 merge, the exact 13-key host
   resource set, and the previous one-shot authorization acknowledgement;
5. delegates exactly one call to `invoke_one_shot_host_runtime`, inside which
   two image inspections, two canonical argv materializations, and at most one
   `Popen` occur;
6. forbids direct image inspection, command materialization, `Popen`, lease
   claim, and container-entrypoint calls from the new module;
7. requires a closed effect boundary immediately before delegation and forbids
   automatic retry;
8. never calls the executor entry point from the verifier or from tests using
   real adapters.

The entry point verifies the static package, acknowledgements, permission,
claim time, resource keys, and absence of output, lease, and staging. Only then
may it delegate once to the existing host invoker. Permission remains closed in
the authoring state.

## Identities

```text
runtime_operation_base_commit=494e6a0b2f10c26b49c90fbb84c23565699a4064
preexecution_head_commit=bb888b900401894441f37fdbbe21c1e25c288366
preexecution_parent_commit=49c4b97e93b47cefbf35576736927ece02c9402b
preexecution_merged_at_utc=2026-07-29T23:21:31Z
preexecution_verification_sha256=sha256:833371b427a5c8a6e602d675711b85b2edc68441b9e5be191321a2911bce6128
runtime_operation_sha256=sha256:0332428014f7f8385c789ba7e7c55d6c2ec03b020e3f83df9ac9714483bb6bf8
operation_file_sha256=sha256:ba9b514980bf5f8629cc6a140a0b95114689020a4cffb8bf3ce4a58fade10247
package_registry_sha256=sha256:d213e051076a1990b268abfd28dcb4d98c699865fc19039ebfece50761f5e46c
module_sha256=sha256:eb337b1f9cd1c95570d7ec22160886a43efe2531c9c5131b7ac29a84123115a4
verifier_sha256=sha256:78fe6cee7af7f3d652a5b16c1d095540a47dd12177d253c1f8d37da0c812fbc4
test_sha256=sha256:76ede6b6f004d9ddab0bca2fb8891bf3d69d7355665e8fb729f2cf3c0c651ee5
```

## Boundaries

```text
EXECUTION_AUTHORIZATION_COMPLETE=true
PREEXECUTION_VERIFICATION_COMPLETE=true
PREEXECUTION_STATIC_CONTRACT_VERIFIED=true
RUNTIME_OPERATION_RECORD_PRESENT=true
RUNTIME_OPERATION_EXECUTOR_ENTRYPOINT_IMPLEMENTED=true
RUNTIME_OPERATION_STATIC_CONTRACT_VERIFIED=true
ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_OPEN=true
PREEXECUTION_IDENTITY_VERIFIED=false
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

After this slice is committed and merged, a separate execution operation may
materialize the exact host resources and claim time and call the new entry
point with explicit permission. Until that separate operation, no dynamic
verification, command materialization, lease write, or [local compute](../glossary_EN.md#term-local-compute) is
permitted. Any mismatch fails closed before delegation, and the existing host
invoker forbids automatic retry after child creation.

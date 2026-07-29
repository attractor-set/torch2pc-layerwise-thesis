# ADR-078: `QW-LC4-E` one-shot engineering invocation operation record

[Russian version](ADR-078-stage3b-qwake-lc4-e-one-shot-engineering-invocation-operation.md)

- **Status:** accepted as operation authoring; [execution](../glossary_EN.md#term-execution) has not started
- **Date:** 29 July 2026
- **Base commit:** `28be77706bc86abaf34f86e9bdcbdcb9cc2810a8`

## Context

PR #138 completed the merge of the one-shot engineering invocation admission.
The admission binds the authorization, immutable image, Torch2PC revision, and
bounded host invoker while deliberately keeping current-[runtime](../glossary_EN.md#term-runtime) verification
and process spawn in a separate operator operation.

That operation requires an immutable record defining the exact dynamic inputs
and launch checks without performing them during authoring.

## Decision

Materialize the two-file package
`stage3b-qwake-lc4-e-one-shot-engineering-invocation-operation-v1`, a pure
verification module, a CLI verifier, and negative tests. The operation record:

1. binds the PR #138 merge commit, both parents, and the full admission package;
2. rebinds the one-shot authorization, image, Torch2PC revision, and host-invoker
   implementation;
3. records the exact set of 13 required host-resource keys;
4. requires two equal image inspections, two equal canonical-argv
   materializations, an unconsumed authorization, and absence of lease, output,
   and staging at the future execution boundary;
5. limits host spawn to one no-shell `Popen` and forbids automatic retry after a
   spawn [attempt](../glossary_EN.md#term-attempt);
6. preserves `PREEXECUTION_IDENTITY_VERIFIED=false` because the current image,
   host resources, and lease timestamp have not been checked;
7. keeps every runtime effect closed.

The verifier does not import the invocation function, inspect an image,
materialize a command, create a child process, or write a lease or output.

## Identities

```text
operation_base_commit=28be77706bc86abaf34f86e9bdcbdcb9cc2810a8
admission_head_commit=a26419057c133972b18a728575426ef510bcf360
admission_parent_commit=3454d12d3cc16c9c50977e2a598e2bc1a8768441
admission_merged_at_utc=2026-07-29T18:08:53Z
admission_sha256=sha256:fe07bc20bf5866d84730df945c2ababc7b5f4f255648c5de6e3185ba4e37c01d
operation_sha256=sha256:10a612ef1b765362b361ecea57923d00a9f7339c9d3f9e3b27337f92f15326e9
operation_file_sha256=sha256:b8cabec098b14f1007adc9fa660fa1e31af9501f2266219aca3ddec24129f610
package_registry_sha256=sha256:eeb417ba5d2c72dc198b22be69ea1d933da5bb03245615d418bbf0a6ba15edbd
module_sha256=sha256:f653468c77494205a6daf7af6ea3cd151260c9b9479b9a02f0a41949a0a5ab30
verifier_sha256=sha256:a51b22004bb8da9611538c01bf718710e5a6eda4111b3dec44aa7dbcb777448c
test_sha256=sha256:bc11ec8443cf7432bb89d6ebbf1698448125c30e3ae74331347a866be17d4458
```

## Boundaries

```text
REPOSITORY_FREEZE_COMPLETE=true
INVOCATION_ADMISSION_COMPLETE=true
INVOCATION_OPERATION_RECORD_PRESENT=true
PREEXECUTION_IDENTITY_CHECKS_IMPLEMENTED=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_OPERATION_OPEN=true
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

A separate slice must commit and merge this record. Only after independent
post-merge verification may a distinct effectful execution operation complete
all dynamic checks and either perform exactly one attempt or fail closed before
spawn.

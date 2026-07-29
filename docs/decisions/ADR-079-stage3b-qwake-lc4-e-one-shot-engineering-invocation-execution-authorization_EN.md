# ADR-079: `QW-LC4-E` one-shot engineering invocation execution authorization

[Russian version](ADR-079-stage3b-qwake-lc4-e-one-shot-engineering-invocation-execution-authorization.md)

- **Status:** accepted as authorization authoring; [runtime](../glossary_EN.md#term-runtime) verification and [execution](../glossary_EN.md#term-execution) have not started
- **Date:** 29 July 2026
- **Base commit:** `b0f6729e8fd1cb1aa172eef488dc56e36b335173`

## Context

PR #139 completed the merge of the one-shot engineering invocation operation
record. That record freezes the dynamic inputs and mandatory future launch
checks while deliberately withholding branch execution permission and leaving
the current image, host resources, claim time, lease, output, and staging
unverified.

A machine-readable authorization is required before a separate runtime
verification. It must bind the exact operation merge to the previously frozen
one-shot permission and define the conditions for exactly one future call.

## Decision

Materialize the two-file package
`stage3b-qwake-lc4-e-one-shot-engineering-invocation-execution-authorization-v1`,
a pure verifier module, a CLI verifier, and negative tests. The authorization:

1. binds the PR #139 merge commit, operation head and parent, and complete
   `operation-v1` package;
2. rebinds the previous one-shot authorization, immutable image, Torch2PC
   revision, and bounded host invoker;
3. authorizes only a future pre-execution verification and one future
   engineering invocation while keeping the authoring branch closed;
4. requires the exact 13 host-resource keys, two equal image inspections, two
   equal canonical-argv materializations, and at most one no-shell `Popen`;
5. requires an unconsumed authorization and absence of lease, output, and
   staging immediately before launch;
6. requires dynamic verification and launch in the same process, forbids a host
   lease write, and forbids automatic retry after spawn;
7. preserves `PREEXECUTION_IDENTITY_VERIFIED=false` and every runtime effect
   until a separate post-merge slice.

The module does not import the invocation function, inspect an image,
materialize a command, create a child process, or write a lease, output, or
[evidence](../glossary_EN.md#term-evidence).

## Identities

```text
execution_base_commit=b0f6729e8fd1cb1aa172eef488dc56e36b335173
operation_head_commit=aa8886221e286a5881f2b720414859bb313c2867
operation_parent_commit=28be77706bc86abaf34f86e9bdcbdcb9cc2810a8
operation_merged_at_utc=2026-07-29T18:57:10Z
operation_sha256=sha256:10a612ef1b765362b361ecea57923d00a9f7339c9d3f9e3b27337f92f15326e9
execution_authorization_sha256=sha256:ff136538faee0d7952dc444e521d7ec760c7d54cd38406cb9b19ff1e00d9437b
authorization_file_sha256=sha256:11f12d2c2723902716ca9e7209f408b9edae2f793ceb098c8adeb06fee8c0c72
package_registry_sha256=sha256:4ab39c084f330d8679495f4aefdcc11005fc8d83a21b2a5c78cee80aeda562b5
module_sha256=sha256:2769982c9f36108f1cb70b43ab7cee9eea5a63ac870f5fb1d4d938800ee837f5
verifier_sha256=sha256:3a4f8f920b1d28036c9f1d690b98f492437de1c2e9ce5106baf102bd05f053bd
test_sha256=sha256:c1b226bc97d4fcd3c5db30ee0c581581dc65da57924c61cb19e4d65daeb29b59
```

## Boundaries

```text
REPOSITORY_FREEZE_COMPLETE=true
INVOCATION_ADMISSION_COMPLETE=true
INVOCATION_OPERATION_COMPLETE=true
EXECUTION_AUTHORIZATION_RECORD_PRESENT=true
EXECUTION_AUTHORIZATION_ISSUED=true
PREEXECUTION_VERIFICATION_MATERIALIZATION_IMPLEMENTED=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_OPERATION_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_EXECUTION_OPEN=true
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

After this authorization is committed and merged, a separate slice may perform
only the current-runtime pre-execution verification. Any mismatch must fail
closed, and that verification cannot create a lease or spawn the container.
The actual one-shot invocation remains a distinct atomic operation.

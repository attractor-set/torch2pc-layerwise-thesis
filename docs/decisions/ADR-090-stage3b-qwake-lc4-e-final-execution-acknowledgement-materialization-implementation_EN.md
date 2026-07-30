# ADR-090: `QW-LC4-E` final-acknowledgement materialization implementation

- **Status:** accepted
- **Date:** 2026-07-30
- **Scope:** `QW-LC4-E`, final operator acknowledgement

## Context

ADR-089 froze the operator-bound future-materialization contract while leaving
the writer uncalled. PR #150 carrying that contract was merged into `main`
`6497cd904f9403622249c5a32f08ef6e8bb11532` and independently verified. The
next stage needs a narrow programmatic adapter between the prospective
materialization and the already verified atomic writer, while keeping the
production call separate.

## Decision

Add a separate implementation module whose import is effect free. Its sole
explicitly called materialization function:

1. revalidates the exact frozen authoring chain and PR #150 post-merge receipt;
2. accepts only an already valid
   `ProspectiveFinalExecutionAcknowledgementMaterialization`;
3. delegates exactly one write to
   `persist_final_execution_acknowledgement`;
4. performs no direct filesystem write;
5. calls the exact persisted-byte verifier exactly once after the write and
   requires complete result equality;
6. creates no lease or durable outcome, performs no image inspection or command
   materialization, invokes no Docker/[runtime](../glossary_EN.md#term-runtime), and consumes no authorization;
7. forbids a production callsite in the current slice and forbids automatic
   retry.

## Current-slice boundary

The materializer implementation is present but is not called. Positive tests
may create an acknowledgement only inside isolated temporary copies of the
minimal repository. The real production path, lease, outcome, and runtime
remain absent.

```text
MATERIALIZATION_AUTHORING_POST_MERGE_VERIFIED=true
ACKNOWLEDGEMENT_MATERIALIZATION_CONTRACT_AUTHORED=true
ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTED=true
MATERIALIZER_CALLED=false
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

After merge and separate post-merge verification, a distinct invocation-
authoring slice may bind the exact operator, issuer, and materializer identities
and timestamps. Merging ADR-090 itself neither creates the acknowledgement nor
permits invocation.

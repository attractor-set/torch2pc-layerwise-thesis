# ADR-076: `QW-LC4-E` one-shot host-runtime-invoker repository freeze

[Russian version](ADR-076-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-repository-freeze.md)

- **Status:** accepted
- **Date:** 29 July 2026
- **Scope:** `QW-LC4-E`, repository boundary before the one-shot engineering invocation

## Context

Implementation `stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-implementation-v1`
was merged through PR #136 into `main` `da51c8d858c541372525125640db99062041fc20`.
Post-merge verification recorded the two exact parents, tree equality with head
`181abda36465d3a91db5970e684938266200a798`, the 16-file scope, two successful
CI checks, 139 targeted tests, and 1186 full tests.

A separate [integrity seal](../glossary_EN.md#term-integrity-sealing) is required
before the operator action. It binds the invoker implementation to one concrete
`main` state without granting branch-level [execution](../glossary_EN.md#term-execution).

## Decision

1. Materialize the two-file
   `stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-repository-freeze-v1`
   receipt.
2. Bind it to PR #136, the exact merge commit, both parents, and merge time.
3. Freeze the implementation semantic digest, invoker contract, module,
   verifier, test, `implementation.json`, registry, and exact Torch2PC revision.
4. Record CI and local verification as engineering-slice identity, not a
   scientific result.
5. Preserve prior [evidence](../glossary_EN.md#term-evidence) unchanged and
   perform neither image inspection nor `docker run` in this slice.
6. Until receipt merge and independent reverification, keep the one-shot
   engineering invocation, lease, authorization consumption, output, and
   publication closed.

## Verifiable boundary

```text
qwake_adr=ADR-076-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-repository-freeze
qwake_host_runtime_invoker_repository_main_commit=da51c8d858c541372525125640db99062041fc20
qwake_host_runtime_invoker_implementation_head=181abda36465d3a91db5970e684938266200a798
qwake_host_runtime_invoker_repository_freeze_materialized=true
qwake_host_runtime_invoker_repository_freeze_complete=false
qwake_next_slice=QW-LC4-E-one-shot-host-runtime-invoker-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC4-E-one-shot-engineering-invocation
HOST_RUNTIME_INVOKER_IMPLEMENTATION_PRESENT=true
HOST_RUNTIME_INVOKER_PRESENT=true
HOST_RUNTIME_INVOKER_EXECUTABLE=true
HOST_DOCKER_RUN_IMPLEMENTED=true
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
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
IMAGE_INSPECTION_PERFORMED=false
DOCKER_RUN_PERFORMED=false
RUNTIME_RERUN_PERFORMED=false
FILES_STAGED=false
```

## Consequences

Only receipt merge and a separate post-merge verification may complete the
repository freeze and permit preparation of the atomic one-shot operator
operation. ADR-076 itself neither invokes the host runner nor consumes the
existing authorization.

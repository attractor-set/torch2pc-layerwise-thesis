# ADR-065: `QW-LC4-E` execution-admission freeze

[Russian version](ADR-065-stage3b-qwake-lc4-e-execution-admission-freeze.md)

- **Status:** accepted as an admission freeze; [execution](../glossary_EN.md#term-execution) has not started
- **Date:** July 27, 2026

## Context

Admission authoring merged through PR #125 into `main` `bce821dff0729629db0ccb306d8f3fd1dd9a2e13` and was
independently verified. One concrete admission record must now be frozen
without creating a lease, executor, result root, or [evidence](../glossary_EN.md#term-evidence).

## Decision

Freeze the five-file
`stage3b-qwake-lc4-e-execution-admission-freeze-v1` package: canonical
`admission.json`, validation log, receipt, and two SHA-256 registries. The
record permits one engineering [attempt](../glossary_EN.md#term-attempt) and binds the exact control-plane
commit.

`runtime_execution_permitted=true` inside the record does not open the
branch-level gate. Before merge and reverification,
`QW_LC4_E_EXECUTION_PERMITTED=false`.

## Exact identities

```text
control_plane_merge_commit=bce821dff0729629db0ccb306d8f3fd1dd9a2e13
control_plane_pr_head=83a07683feb51913c7fcc7878a323e51a84da771
torch2pc_commit=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
admitted_at_utc=2026-07-27T20:58:25Z
admission_sha256=sha256:d1ee6d022588f0a2cf0ac23f3bf8de9b27f9aad4fc1153435bd70e1ab83e296c
admission_file_sha256=sha256:d819f8a7e03314242c0072e2d020a59fbe6b7f6984fda99ff0dcd306cc97ca70
verification_receipt_file_sha256=sha256:d4b9d33117cbf522b1c62173c7a81f9638cde703eb6b3bbb392ff46e45a17c25
package_registry_sha256=sha256:411f3e8d62b367755a6f02070ad84bc6f37cfefad602d885674a844b57aa74cd
source_registry_sha256=sha256:01c9a29d1f80098707d6715ffd5160ad48bb497b08a71180c2b71d8e89b66504
authorized_output_root=results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001
```

## Boundaries

```text
QW_LC4_E_AUTHORING_MERGED=true
ADMISSION_FREEZE_BRANCH_OPEN=true
ADMISSION_FREEZE_MATERIALIZED=true
EXECUTION_ADMISSION_ISSUED=true
ADMISSION_RECORD_RUNTIME_EXECUTION_PERMITTED=true
QW_LC4_E_EXECUTION_PERMITTED=false
AUTHORIZATION_CONSUMED=false
EXECUTION_LEASE_PRESENT=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

This slice permits only the admission-freeze commit and PR. After merge, the
tree and package must be independently reverified. Only then may a separate
one-attempt lease and execution-wrapper authoring slice open.

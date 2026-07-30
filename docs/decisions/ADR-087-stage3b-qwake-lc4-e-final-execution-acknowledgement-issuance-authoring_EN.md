# ADR-087: final `QW-LC4-E` acknowledgement issuance authoring

[Russian version](ADR-087-stage3b-qwake-lc4-e-final-execution-acknowledgement-issuance-authoring.md)

- **Status:** accepted as a static issuance contract; acknowledgement not issued
- **Date:** 2026-07-30
- **Base commit:** `eb20c157584efff8e9aa0418385242c7d7b26eab`

## Context

PR #147 froze a machine-verifiable format for a future operator
acknowledgement and was independently verified after merge. The format binds
the exact phrase, operator, time, [evidence](../glossary_EN.md#term-evidence) chain, image, Torch2PC, output root,
and one [attempt](../glossary_EN.md#term-attempt). It does not yet define safe durable issuance of the
acknowledgement file.

Issuance must be separate from format authoring, writer implementation, lease
materialization, and invocation. Failure, collision, or identity drift must not
produce a partially issued acknowledgement or automatically permit [execution](../glossary_EN.md#term-execution).

## Decision

1. Add the static issuance-authoring package
   `stage3b-qwake-lc4-e-final-execution-acknowledgement-issuance-authoring-v1`.
2. Preserve the exact PR #147 post-merge validation receipt: `50` focused,
   `251` targeted, and `1298` full tests with `14` warnings, required CI checks,
   Ruff, `mypy`, both MkDocs builds, Torch2PC identity, and the closed
   production boundary.
3. Bind issuance to the exact ADR-086 package, its semantic and file identity,
   source registries, module, verifier, test, and both ADR versions.
4. Freeze the sole future acknowledgement path
   `results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001.final-execution-acknowledgement.json`.
5. Require the exact operator phrase, operator identity, and acknowledgement
   time strictly after PR #147 merge, plus a separate issuer identity and an
   issuance time not before acknowledgement time.
6. Require future implementation to use canonical JSON bytes, exclusive atomic
   no-overwrite persistence, mode `0600`, file and directory `fsync`, a
   pre-existing non-symbolic parent, temporary cleanup, and exact persisted-byte
   reverification.
7. Limit issuance to one attempt with no retry. Even successful future issuance
   must not automatically create a lease, consume authorization, inspect the
   image, materialize a command, or permit invocation.
8. Do not write an acknowledgement, create a lease, inspect the image,
   materialize a command, spawn a process, or invoke Docker in this slice.

## Identities

```text
acknowledgement_authoring_pr=147
acknowledgement_authoring_head=d75a767c714da7437ceef2be78c0c5ee479d66b2
acknowledgement_authoring_base=2957d8f6975c88e7bdb23243e3915c7f51d4ba47
acknowledgement_authoring_merge=eb20c157584efff8e9aa0418385242c7d7b26eab
acknowledgement_authoring_merged_at_utc=2026-07-30T16:03:05Z
acknowledgement_authoring_focused_tests=50
acknowledgement_authoring_targeted_tests=251
acknowledgement_authoring_full_tests=1298
acknowledgement_authoring_full_test_warnings=14
acknowledgement_authoring_sha256=sha256:fb76d1c483a5ba15ca629edd6b2866eac0d497fd3569241a0c78fddbb5c50cd7
acknowledgement_relative=results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001.final-execution-acknowledgement.json
file_mode=0600
invocation_count=1
```

## Boundary

```text
FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_POST_MERGE_VERIFIED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORED=true
ACKNOWLEDGEMENT_ISSUANCE_CONTRACT_AUTHORED=true
ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTED=false
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

The repository gains a verifiable contract for future issuance, but not a
writer and not an issued acknowledgement. After merge and reverification, the
next admissible stage is a separate atomic issuance implementation. Actual
acknowledgement materialization and the subsequent lease remain distinct
slices.

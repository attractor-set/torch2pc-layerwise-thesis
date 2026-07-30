# ADR-083: persistent evidence chain v2 for `QW-LC4-E`

[Russian version](ADR-083-stage3b-qwake-lc4-e-persistent-evidence-chain-v2.md)

- **Status:** accepted as an authoring contract; [execution](../glossary_EN.md#term-execution) blocked
- **Date:** July 30, 2026
- **Base commit:** `5e61ed650c9beda2cde1f58650345f01694836f6`

## Context

PR #143 repaired the corrected [runtime](../glossary_EN.md#term-runtime)-operation module identity and was
independently verified after merge. The earlier `execution-lease-v1`, however,
bound an older admission freeze and did not contain the complete current chain:
invocation authorization, execution authorization, pre-execution verification,
runtime operation, and runtime-operation identity repair.

The terminal host outcome was also represented only in memory. A pre-spawn
rejection, spawn failure, nonzero return code, timeout, or signal had no required
persistent receipt preserving the [attempt](../glossary_EN.md#term-attempt) boundary and forbidding retry.

## Decision

1. Add the persistent authoring package
   `stage3b-qwake-lc4-e-persistent-evidence-chain-v2-authoring-v1`.
2. Preserve a full post-merge PR #143 validation receipt: `24` focused,
   `201` targeted, and `1248` full tests with `14` warnings, required CI checks,
   Ruff, mypy, both MkDocs builds, Torch2PC identity, and the closed runtime
   boundary.
3. Define a pure `persistent-execution-lease-v2` template that must bind:
   - invocation authorization id/SHA/merge;
   - execution authorization id/SHA/merge;
   - pre-execution verification id/SHA/merge;
   - runtime operation id/SHA/merge;
   - identity repair id/SHA/merge;
   - corrected runtime-operation module SHA;
   - immutable image repository digest;
   - Torch2PC commit;
   - output root, lease path, and outcome path;
   - `claimed_at_utc` and `invocation_count=1`.
4. Define a pure `durable-host-outcome-receipt` required after every successful
   lease-v2 claim, including negative outcomes before and after spawn. The
   receipt records start/end UTC, termination class, return code when available,
   child spawn count, full-stream stdout/stderr SHA-256, total and captured
   byte counts, a consistent truncation flag, before/after output-root snapshots,
   lease persistence, and `retry=false`.
5. Require a lease-bound capability for any future lower-level host-invoker call
   and forbid bypassing the top-level runtime operation.
6. Do not implement lease writing, outcome writing, capability wiring, image
   inspection, materialization, spawn, or Docker in this slice. Those belong to
   a separate implementation slice after this authoring contract is merged.

## Identities

```text
identity_repair_pr=143
identity_repair_head=d7a5c121b2f7e56155603bbfbf98f3713f0c0e87
identity_repair_merge=5e61ed650c9beda2cde1f58650345f01694836f6
identity_repair_merged_at_utc=2026-07-30T02:21:08Z
post_merge_validation_receipt_sha256=sha256:d593c1df66d046e97f19f252e0c8056daf19d48e8957a7b66075ec0d8d3c095a
persistent_evidence_chain_v2_sha256=sha256:c0a6195080cec64e6104a90076366cc2bfa10a723b45a7389cd77fa1b3b11bd1
image_repo_digest=torch2pc-layerwise-thesis@sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d
torch2pc_commit=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
invocation_count=1
```

## Boundaries

```text
CORRECTED_FULL_VALIDATION_RECEIPT_PRESENT=true
RUNTIME_OPERATION_IDENTITY_REPAIR_MERGED=true
LATEST_AUTHORIZATION_BOUND_IN_PERSISTENT_LEASE_TEMPLATE=true
DURABLE_NEGATIVE_HOST_OUTCOME_DEFINED=true
PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=false
DURABLE_OUTCOME_WRITER_IMPLEMENTED=false
LEASE_BOUND_HOST_INVOKER_ENFORCED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

Two previously incomplete requirements now have machine-checkable forms: the
complete persistent lease v2 and a durable terminal receipt including negative
outcomes. This closes the design-contract gap but does not open execution. A
separate implementation of atomic persistence, capability wiring, fail-safe
outcome writing, and a new [final execution](../glossary_EN.md#term-final-execution) authorization remains mandatory.

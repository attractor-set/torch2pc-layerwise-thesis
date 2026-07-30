# ADR-086: final `QW-LC4-E` execution acknowledgement authoring

[Russian version](ADR-086-stage3b-qwake-lc4-e-final-execution-acknowledgement-authoring.md)

- **Status:** accepted as a static authoring contract; acknowledgement not issued
- **Date:** 2026-07-30
- **Base commit:** `2957d8f6975c88e7bdb23243e3915c7f51d4ba47`

## Context

PR #146 bound the host invoker to the exact persisted bytes of persistent
[execution](../glossary_EN.md#term-execution) lease v2 and was independently verified after merge. The chain now
contains atomic lease persistence, a durable terminal receipt, and one
prospective entrypoint without direct lower-level invoker bypass.

Static mechanism readiness is not a final operator acknowledgement. Automatic
transition from an authored contract to a permitted invocation is forbidden:
the acknowledgement must separately and unambiguously bind the operator, time,
complete [evidence](../glossary_EN.md#term-evidence) chain, image, Torch2PC, output root, and one irreversible
[attempt](../glossary_EN.md#term-attempt).

## Decision

1. Add the static authoring package
   `stage3b-qwake-lc4-e-final-execution-acknowledgement-authoring-v1`.
2. Preserve the exact PR #146 post-merge validation receipt: `39` focused,
   `240` targeted, and `1287` full tests with `14` warnings, required CI checks,
   Ruff, `mypy`, both MkDocs builds, Torch2PC identity, and the closed [runtime](../glossary_EN.md#term-runtime)
   boundary.
3. Bind the authoring contract to `persistent-evidence-chain-v2`, its
   implementation, host-invoker wiring, invocation authorization, execution
   authorization, pre-execution verification, runtime operation, and runtime
   operation identity repair.
4. Require the exact phrase
   `ACKNOWLEDGE_QWAKE_LC4_FINAL_ONE_SHOT_EXECUTION`, a non-empty operator
   identity, and a UTC timestamp strictly after PR #146 was merged.
5. Bind the future acknowledgement to the exact immutable image, Torch2PC
   commit, output root, lease v2 path, durable outcome path,
   `invocation_count=1`, no retry, and one attempt.
6. Separate authoring, acknowledgement issuance, and lease materialization.
   The presence of this ADR and package does not issue an acknowledgement and
   does not permit invocation.
7. Do not write an acknowledgement, create a lease, inspect the image,
   materialize a command, consume authorization, spawn a process, or invoke
   Docker in this slice.

## Identities

```text
wiring_pr=146
wiring_head=1d4096a8086c9f9c32e1d14515ef3b702d2237ab
wiring_base=0303a1514e2875a057ef1b20293a01b36a9c6b2b
wiring_merge=2957d8f6975c88e7bdb23243e3915c7f51d4ba47
wiring_merged_at_utc=2026-07-30T14:37:25Z
wiring_focused_tests=39
wiring_targeted_tests=240
wiring_full_tests=1287
wiring_full_test_warnings=14
persistent_evidence_chain_v2_sha256=sha256:c0a6195080cec64e6104a90076366cc2bfa10a723b45a7389cd77fa1b3b11bd1
persistent_evidence_chain_v2_implementation_sha256=sha256:3671f7b12b570e7caace38dec0e023691bc1051b3cbf8e72ddfda59058369362
lease_bound_host_invoker_wiring_sha256=sha256:a064b518b960159d0fe7d9178962ecab5d2c1660deddffb3155c76db7d937655
image_repo_digest=torch2pc-layerwise-thesis@sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d
torch2pc_commit=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
invocation_count=1
```

## Boundary

```text
WIRING_POST_MERGE_VERIFIED=true
PERSISTENT_EVIDENCE_CHAIN_V2_PRESENT=true
PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=true
DURABLE_OUTCOME_WRITER_IMPLEMENTED=true
LEASE_BOUND_HOST_INVOKER_ENFORCED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORED=true
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

The repository gains a machine-verifiable format for a future final
acknowledgement, but not the acknowledgement itself. After this package is
merged and reverified, the next admissible stage is a separate acknowledgement
issuance slice. Even an issued acknowledgement must not automatically create a
lease or start the runtime: materialization and invocation remain separate
fail-closed atomic actions.

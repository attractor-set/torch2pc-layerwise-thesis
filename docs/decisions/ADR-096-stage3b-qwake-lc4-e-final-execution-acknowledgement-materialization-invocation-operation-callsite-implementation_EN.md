# ADR-096: production-callsite implementation for the acknowledgement-materialization operator operation

- Status: accepted
- Date: 2026-08-01
- Decision: implement the single production command interface frozen by ADR-095 without executing it in the primary worktree or opening permission for the operation.

## Context

PR #162 merged as `b27e252cf7c64e88d5d61bf7a23c70ffc5957959` after `main` had advanced. Independent reconciliation established actual first parent `dc8dc200515959858d43b68984dbd87f27f3446c`, original base `23a86cc0769f20b4b7536e64250f3dee062aaa62`, exact first-parent delta `18/1516/0`, and deterministic merge-tree equality at `408c9cbbd97c35292ba8a9476c54d3fe0905f00e`.

ADR-095 froze the path, symbol, explicit inputs, and sole delegate. The callsite file did not exist before this slice.

## Decision

Add exactly one production file:

```text
scripts/invoke_stage3b_qwake_lc4_final_execution_acknowledgement_materialization_operation.py
```

Its `main` requires both explicit options:

```text
--project-root
--operation-json
```

The operation input must be a regular non-symlink file containing the exact canonical JSON and complete field set of the prospective operation. Standard input, environment [fallback](../glossary_EN.md#term-fallback), interactive prompts, and implicit defaults are forbidden.

After structural and canonical validation, the command interface calls exactly once:

```text
torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_implementation.perform_final_execution_acknowledgement_materialization_invocation_operation
```

Standalone durable-state probing and direct calls to the adapter, materializer, or writer are forbidden. Automatic and blind retry are absent.

The successful result is rechecked for exact operation, single-call, no-retry, and closed-[execution](../glossary_EN.md#term-execution) flags. Only then is canonical result JSON emitted to standard output. No result file is written. Any failure returns nonzero and emits no partial result on standard output.

## Verification without production execution

The implementation package and static verifier import and inspect the callsite without invoking the operation. Behavioural tests either replace the sole delegate or run the complete path only in an isolated temporary repository copy. The primary worktree receives no acknowledgement, lease, outcome, or [runtime](../glossary_EN.md#term-runtime) [evidence](../glossary_EN.md#term-evidence).

The historical ADR-094/ADR-095 source registries and tests remain byte-identical. A shared `tests/conftest.py` creates an isolated temporary view without the successor callsite for those two historical modules, so their absence assertions still verify their own frozen slice while the current production implementation is not altered.

## Closed boundary

```text
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_IMPLEMENTED=true
PRODUCTION_CALLSITE_PRESENT=true
MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false
INVOCATION_ADAPTER_CALLED=false
MATERIALIZATION_INVOKED=false
MATERIALIZER_CALLED=false
WRITER_CALLED=false
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

The command interface is not permission to run it. After merge, only a separate callsite-execution authoring slice may open. That slice must form and separately authorize the canonical operation file; this implementation alone neither creates the acknowledgement nor consumes authority.

# ADR-097: authoring execution of the production callsite for acknowledgement materialization

- Status: accepted
- Date: 2026-08-01
- Decision: freeze a separate verifiable contract for one future [execution](../glossary_EN.md#term-execution) of the implemented production callsite without authorizing or performing that execution.

## Context

PR #163 implemented the production callsite and was independently verified after merge as `78129528d05e8268b4e40fdf708fd9d2c8e3ab29`. The presence of an executable file does not permit its execution. The current branch contains no execution authorization, canonical operation file, or permission to create the acknowledgement.

## Decision

Future execution is bound to the exact file:

```text
scripts/invoke_stage3b_qwake_lc4_final_execution_acknowledgement_materialization_operation.py
```

and a separate action phrase:

```text
EXECUTE_QWAKE_LC4_FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_CALLSITE
```

A future authorization must separately bind the operator identity, timestamp, exact SHA-256 of canonical `operation.json`, and execution commit. The operation file and authorization remain absent in this slice. Authorization must merge and pass independent post-merge verification before any execution [attempt](../glossary_EN.md#term-attempt).

Immediately before the single attempt, the exact commit, Torch2PC revision, clean worktree and index, callsite SHA-256, operation-file SHA-256, and absence of acknowledgement, both leases, durable outcome, [runtime](../glossary_EN.md#term-runtime) output, and staging must be reverified. The command must run without shell interpretation, from the exact project root, with explicit `--project-root` and `--operation-json`. Automatic and blind retry are forbidden.

Success requires a zero exit code and exactly one canonical JSON object on standard output. Output before verified success and a separate result file are forbidden.

## Closed boundary

```text
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_AUTHORIZED=false
PRODUCTION_CALLSITE_PRESENT=true
PRODUCTION_CALLSITE_EXECUTED=false
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_PERFORMED=false
MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false
INVOCATION_ADAPTER_CALLED=false
MATERIALIZER_CALLED=false
WRITER_CALLED=false
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

After merge, only a separate execution-authorization slice may open. This ADR does not permit creation of `operation.json`, callsite execution, operation performance, acknowledgement creation, Docker use, or [local compute](../glossary_EN.md#term-local-compute).

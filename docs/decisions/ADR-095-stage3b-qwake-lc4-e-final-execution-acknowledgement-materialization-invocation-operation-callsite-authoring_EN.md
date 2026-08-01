# ADR-095: authoring the production callsite for the acknowledgement-materialization operator operation

- Status: accepted
- Date: 2026-07-31
- Decision: freeze a separate verifiable contract for the future production callsite without adding that callsite or performing the operation.

## Context

PR #155 implemented the library operator operation and was independently verified after merge as `23a86cc0769f20b4b7536e64250f3dee062aaa62`. The repository still contains no production callsite. Merging a library implementation must not implicitly authorize acknowledgement creation.

## Decision

The future callsite is bound to exactly one path:

```text
scripts/invoke_stage3b_qwake_lc4_final_execution_acknowledgement_materialization_operation.py
```

and exactly one delegate:

```text
torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_implementation.perform_final_execution_acknowledgement_materialization_invocation_operation
```

The future CLI accepts only explicit `--project-root` and `--operation-json` inputs. The operation file must contain the canonical prospective object. Standard input, environment [fallback](../glossary_EN.md#term-fallback), interactive confirmation, and implicit defaults are forbidden. The delegate may be called at most once. Standalone pre-probing, direct adapter, materializer, or writer calls, and automatic or blind retry are forbidden.

Success is allowed only after the operation result verifies; the canonical result is emitted to standard output. Writing a separate result file is forbidden. Callsite implementation and later operation performance remain separate slices.

## Closed boundary

```text
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_IMPLEMENTED=false
PRODUCTION_CALLSITE_PRESENT=false
MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false
INVOCATION_ADAPTER_CALLED=false
MATERIALIZATION_INVOKED=false
MATERIALIZER_CALLED=false
WRITER_CALLED=false
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
EXECUTION_LEASE_MATERIALIZED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

After merge, only a separate callsite-implementation slice may open. This ADR does not permit creation of the callsite file, operation performance, acknowledgement materialization, Docker use, or [local compute](../glossary_EN.md#term-local-compute).

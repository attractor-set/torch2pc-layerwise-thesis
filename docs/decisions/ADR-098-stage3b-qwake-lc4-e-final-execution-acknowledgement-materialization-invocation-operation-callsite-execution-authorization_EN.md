# ADR-098: production-callsite execution authorization

- **Status:** accepted
- **Date:** 2026-08-02
- **Context:** `QW-LC4-E`
- **Preceded by:** ADR-097

## Context

ADR-097 froze the requirements for one future [execution](../glossary_EN.md#term-execution) of the implemented production callsite. After independent verification of PR #164, a separate machine-readable slice is required to bind the exact operator, canonical operation object, and callsite identity without performing the action.

## Decision

Create one frozen `execution-authorization-v1` package containing:

1. `execution-authoring-merge-validation.json` with the exact post-merge receipt for PR #164;
2. `operation.json`, the canonical prospective operation object;
3. `authorization.json`, a single-use authorization pinned to the SHA-256 of `operation.json`;
4. `source-SHA256SUMS` and `SHA256SUMS`.

The authorization freezes operator `dzmitry-prychyna`, a distinct authorization phrase, the exact production-callsite path and SHA-256, the argv template, `invocation_count=1`, no shell interpretation, and no retry.

## Effective-state semantics

The presence of `authorization.json` means that authorization has been issued but is not yet effective. It may become a basis for execution only after:

- this slice is merged;
- the exact merge commit is independently verified;
- the callsite and `operation.json` SHA-256 identities are reverified;
- a clean worktree and absence of acknowledgement, leases, durable outcome, result directory, and temporary files are confirmed.

Before post-merge verification:

```text
EXECUTION_AUTHORIZATION_ISSUED=true
EXECUTION_AUTHORIZATION_POST_MERGE_VERIFIED=false
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_AUTHORIZED=false
AUTHORIZATION_CONSUMED=false
PRODUCTION_CALLSITE_EXECUTED=false
```

## Single-use semantics

The authorization permits one [attempt](../glossary_EN.md#term-attempt) only. Consumption must be atomic with attempt start. After consumption, automatic, blind, or manual retry under the same record is forbidden, including failure after an uncertain result.

## Effect boundary

This slice does not execute the production callsite, call the library operation, adapter, materializer, or writer, create the final acknowledgement, or open [local compute](../glossary_EN.md#term-local-compute).

## Consequences

After merge and independent authorization verification, a separate one-shot execution slice may be opened. Merge alone is not execution and does not consume authorization.

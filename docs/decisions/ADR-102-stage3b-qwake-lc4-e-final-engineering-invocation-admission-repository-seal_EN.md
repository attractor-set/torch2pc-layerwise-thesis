# ADR-102: `QW-LC4-E` final engineering-invocation admission repository seal

[Russian version](ADR-102-stage3b-qwake-lc4-e-final-engineering-invocation-admission-repository-seal.md)

- **Status:** accepted as repository-seal authoring; [execution](../glossary_EN.md#term-execution) closed
- **Date:** 2026-08-03
- **Context:** `QW-LC4-E`
- **Preceded by:** ADR-101
- **Verified `main`:** `d2539eb440e758c1f29b935f8599561bec7126bc`

## Context

ADR-101 materialized the pure schema and canonical final engineering-invocation
admission record. PR #169 was merged with a merge commit: its exact head is
`b81c11971f1e9b78e59dd39c4d182722a3001044` and post-merge `main` is `d2539eb440e758c1f29b935f8599561bec7126bc`. Independent post-merge verification
confirmed the two-commit graph, exact 17-file scope, acceptable final-head
checks, `ruff`, four static guards, and 23 targeted tests.

The admission record cannot yet ground an authorization. A separate repository
seal must first bind it to one concrete verified `main` state, be merged, and be
independently verified again.

## Decision

1. Materialize the two-file
   `stage3b-qwake-lc4-e-final-engineering-invocation-admission-repository-seal-v1`
   package.
2. Bind the receipt to PR #169, the exact merge commit, both merge parents,
   merge time, both PR commits, and the 17-file scope.
3. Freeze the admission semantic digest and the SHA-256 identities of the
   admission record, registries, module, verifier, and corrected test.
4. Record only verified repository engineering state, not [runtime](../glossary_EN.md#term-runtime) artifacts or a
   scientific result.
5. Keep the new authorization, operator phrase, invocation command, lease v2,
   durable host outcome, and runtime output absent.
6. Until this seal is merged and independently verified, prohibit even the
   separate authoring of the new one-shot authorization.

## Repository receipt

```text
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-repository-seal-v1/receipt.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-repository-seal-v1/SHA256SUMS
```

It preserves:

```text
FINAL_ENGINEERING_INVOCATION_ADMISSION_PR=169
FINAL_ENGINEERING_INVOCATION_ADMISSION_PR_HEAD=b81c11971f1e9b78e59dd39c4d182722a3001044
FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_MAIN_COMMIT=d2539eb440e758c1f29b935f8599561bec7126bc
FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_SEAL_MATERIALIZED=true
FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_SEAL_COMPLETE=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORING_PERMITTED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=false
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
QW5_TRANSITION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
PUBLICATION_PERMITTED=false
```

## Non-executing boundary

This slice neither imports nor calls `invoke_lease_bound_host_runtime`, does not
inspect the image or call Docker, creates no child process, and does not modify
the runtime boundary. It only materializes a verifiable repository receipt and
documentation.

## Sequence

```text
admission authoring merged and verified
→ admission repository seal authoring
→ repository-seal merge and independent verification
→ distinct one-shot authorization authoring
→ authorization merge and independent verification
→ atomic authorization consumption, attempt start, and lease v2
→ invoke_lease_bound_host_runtime
→ durable host outcome
→ sealed extension engineering report
→ QW-5 eligibility decision
```

## Consequences

The repository seal is materialized but not complete until its own merge and
independent verification. No authorization exists and its authoring is not yet
permitted. `QW-5`, the scientific campaign, test split, and publication remain
closed.

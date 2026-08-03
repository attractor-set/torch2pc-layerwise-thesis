# ADR-099: transition after `QW-LC4-E` final-acknowledgement materialization

[Russian version](ADR-099-stage3b-qwake-lc4-e-post-acknowledgement-transition.md)

- **Status:** accepted as a transition contract; engineering invocation not performed
- **Date:** 2026-08-02
- **Context:** `QW-LC4-E`
- **Preceded by:** ADR-098
- **Base commit:** `c9588661e28f2eba81a9da082935968e9224a257`

## Context

ADR-098 issued a separate single-use authorization for the production callsite
that materializes the final operator acknowledgement. After merge, that
callsite was executed once. The authorization is consumed, the acknowledgement
is materialized and verified, and retry of the same [attempt](../glossary_EN.md#term-attempt) is forbidden.

The executed callsite concerns acknowledgement materialization only. It is not
the one-shot `QW-LC4-E` extension engineering invocation: no persistent lease
v2, durable host-outcome receipt, or [runtime](../glossary_EN.md#term-runtime) output exists.

The experimental plan permits transition to `QW-5` only after a successful
`QW-LC4-E` engineering report. The materialized acknowledgement is therefore a
required input to the future invocation, but it does not replace that invocation
or its report.

## Verified state

The sealed [evidence](../glossary_EN.md#term-evidence) package proves:

```text
ACKNOWLEDGEMENT_CALLSITE_ATTEMPT_STARTED=true
ACKNOWLEDGEMENT_CALLSITE_AUTHORIZATION_CONSUMED=true
ACKNOWLEDGEMENT_CALLSITE_SINGLE_ATTEMPT_COMPLETED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=true
FINAL_EXECUTION_ACKNOWLEDGED=true
ACKNOWLEDGEMENT_CALLSITE_RETRY_PERMITTED=false
ACKNOWLEDGEMENT_CALLSITE_REINVOCATION_FORBIDDEN=true
```

The same package proves the absence of engineering-invocation effects:

```text
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
EXTENSION_ENGINEERING_REPORT_PRESENT=false
```

The `callsite_invocation_pending=true` field in the consumption receipt records
the attempt-start state. Terminal `verification.json` separately proves
`single_attempt_completed_state_evidence_verified=true` and the materialized
acknowledgement.

## Decision

1. Treat the materialization-callsite line as complete, consumed, and
   non-reusable.
2. Do not classify its evidence package as the extension engineering report.
3. Keep `QW-5`, `C1`, `C2`, `C3`, `R`, test-data access, and publication closed.
4. Forbid reinvocation of the executed production callsite, repeated
   authorization consumption, and automatic or manual retry based on the same
   record.
5. Permit only a separate future authoring slice for admission of the actual
   one-shot engineering invocation through the lease-bound host invoker.
6. Require that future slice to bind the materialized acknowledgement,
   persistent evidence chain v2, exact image, Torch2PC, output root, and a new
   distinct single-use permission.
7. Create no lease, host outcome, runtime output, Docker command, or scientific
   result in this transition slice.
8. Preserve all existing frozen packages and evidence unchanged.

## Next admissible slice

```text
next_slice=QW-LC4-E-final-engineering-invocation-admission-authoring
```

That future authoring slice does not execute the model. It only freezes a
machine-readable admission for one future atomic operation that points to
`invoke_lease_bound_host_runtime` and requires the already materialized final
acknowledgement.

## Machine boundary

```text
QW_LC4_E_ACKNOWLEDGEMENT_LINE_COMPLETE=true
QW_LC4_E_ACKNOWLEDGEMENT_AUTHORIZATION_CONSUMED=true
QW_LC4_E_ACKNOWLEDGEMENT_RETRY_PERMITTED=false
QW_LC4_E_ACKNOWLEDGEMENT_REINVOCATION_FORBIDDEN=true
QW_LC4_E_EXTENSION_ENGINEERING_REPORT_PRESENT=false
QW_LC4_E_COMPLETE=false
QW5_TRANSITION_PERMITTED=false
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

The transition branch is not a `QW-5` branch. It freezes the distinction between
completed acknowledgement materialization and the still-absent extension
engineering report. The next invocation requires its own admission,
authorization, terminal evidence, and repository seal.

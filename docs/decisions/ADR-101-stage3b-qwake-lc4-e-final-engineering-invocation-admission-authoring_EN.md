# ADR-101: final `QW-LC4-E` engineering-invocation admission authoring

[Russian version](ADR-101-stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring.md)

- **Status:** accepted as admission authoring; [execution](../glossary_EN.md#term-execution) closed
- **Date:** 2026-08-03
- **Context:** `QW-LC4-E`
- **Preceded by:** ADR-100
- **Base commit:** `5ee7d33b2d6a9092b2db473040b92ad8cda7e08f`

## Context

ADR-100 froze the admission-authoring scope after PR 168 was merged. It bound
exact source packages, the immutable image, persistent [evidence](../glossary_EN.md#term-evidence) chain v2, and
the sole prospective `invoke_lease_bound_host_runtime` entrypoint. The scope
freeze created no admission record, authorization, lease, or [runtime](../glossary_EN.md#term-runtime) output.

This slice must materialize a verifiable admission record without turning it
into permission to [run](../glossary_EN.md#term-run). A later distinct slice
must seal and independently verify the exact repository commit before issuing a
new one-shot authorization.

## Decision

Add the pure
`stage3b_qwake_lc4_final_engineering_invocation_admission.py` schema, a separate
verifier, unit tests, and canonical `admission.json` record.

The schema:

1. verifies the exact SHA-256 identities of five frozen source packages and
   critical files;
2. verifies the completed acknowledgement line and its reinvocation ban;
3. binds the immutable image, output root, lease v2, durable host outcome, and
   sole prospective entrypoint;
4. requires a new distinct authorization for at most one
   [attempt](../glossary_EN.md#term-attempt);
5. keeps authorization, invocation permission, and every runtime effect closed;
6. rejects an existing output root, lease v1 or v2, or durable host outcome;
7. neither imports nor invokes the runtime entrypoint.

## Admission record

```text
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-v1/admission.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-v1/SHA256SUMS
```

The record has its own semantic SHA-256, binds base commit
`5ee7d33b2d6a9092b2db473040b92ad8cda7e08f`, and preserves:

```text
FINAL_ENGINEERING_INVOCATION_ADMISSION_AUTHORED=true
FINAL_ENGINEERING_INVOCATION_ADMISSION_RECORD_PRESENT=true
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
```

## Authorization boundary

This slice reserves no operator phrase and creates no authorization identifier.
A future authorization must be new, distinct from historical permissions, and
valid only after the admission repository seal is merged and independently
verified. Consumption must be atomic with the start of the sole attempt and the
exclusive creation of persistent lease v2.

## Non-executing boundary

The verifier does not import the runtime-entrypoint module and does not call
`invoke_lease_bound_host_runtime`. Negative tests mutate temporary copies only.
This slice performs no image inspection, command materialization, Docker run,
model invocation, child-process creation, or runtime-artifact creation.

## Sequence

```text
admission-authoring
→ admission repository seal and independent verification
→ distinct one-shot authorization
→ atomic authorization consumption and persistent lease v2
→ invoke_lease_bound_host_runtime
→ durable host outcome
→ sealed extension engineering report
→ QW-5 eligibility decision
```

## Consequences

The admission record exists and is verifiable, but it is not an authorization.
The next admissible slice must seal its exact repository commit. `QW-5`, the
scientific campaign, test split, and publication remain closed.

# ADR-089: `QW-LC4-E` final-acknowledgement materialization authoring

- **Status:** accepted
- **Date:** 2026-07-30
- **Scope:** `QW-LC4-E`, final operator acknowledgement

## Context

PR #149 implementing the atomic acknowledgement writer was merged as
`31206012ef7cbd2b7b21a2017374c11123abd42c` and independently verified. The
writer exists, but no production callsite or acknowledgement file exists.
Before any production-state mutation, the exact operator data, temporal order,
and [evidence](../glossary_EN.md#term-evidence) binding for the sole admissible materialization must be frozen
separately.

## Decision

Introduce a static fail-closed materialization-authoring contract:

1. Only the exact PR #149 implementation identity, package, source, tests, and
   documentation may be used as the source.
2. The future record must contain the exact phrase
   `ACKNOWLEDGE_QWAKE_LC4_FINAL_ONE_SHOT_EXECUTION`, distinct operator and issuer
   identities, and an explicit materializer identity.
3. The materializer must equal the issuer, binding the production mutation to
   explicitly named responsibility.
4. Operator acknowledgement must be strictly after the PR #149 merge; issuance
   cannot precede acknowledgement, and materialization cannot precede issuance.
5. The exact path, canonical envelope bytes, SHA-256, writer symbol, and mode
   `0600` must be bound.
6. The target must be absent, its parent must preexist without symbolic
   components, publication must be atomic and no-overwrite, file and directory
   `fsync` are mandatory, temporary cleanup is required, and persisted bytes
   must be reverified exactly.
7. Authoring does not call the writer. Actual materialization, lease, image
   inspection, command construction, Docker, and [local compute](../glossary_EN.md#term-local-compute) remain separate.
8. At most one materialization is admissible; retry and replacement are
   forbidden.

## Consequences

The schema and provenance of the future state mutation become independently
verifiable while the production acknowledgement remains absent. The contract
does not permit invocation, consume authorization, or open local compute.

## Verifiable state

```text
ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTATION_POST_MERGE_VERIFIED=true
ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTED=true
ACKNOWLEDGEMENT_MATERIALIZATION_CONTRACT_AUTHORED=true
ACKNOWLEDGEMENT_MATERIALIZATION_IMPLEMENTED=false
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

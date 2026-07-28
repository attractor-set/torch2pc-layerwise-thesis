# ADR-068: `QW-LC4-E` execution-freeze authoring

[Russian version](ADR-068-stage3b-qwake-lc4-e-execution-freeze-authoring.md)

- **Status:** accepted as fail-closed authoring; actual [execution](../glossary_EN.md#term-execution) remains prohibited
- **Date:** 28 July 2026

## Context

PR #128 containing the atomic lease/wrapper implementation merged into `main`
as `24966cd2a0380e46ab1924ff4ab8987f17e1fe9e`. Its second parent is
`15588616c24d523f1c983fc205aeaae32a33958e`; the exact 16-file tree,
content identities, and two CI checks passed independent verification.

The implementation provides atomic ownership claim, an isolated wrapper,
canonical receipts, and no-replace result promotion. The repository still
lacks two components required for a real engineering [attempt](../glossary_EN.md#term-attempt):

1. a concrete backend that obtains real FixedPred states and produces the
   168 matched cells plus 28 reserve probes;
2. a one-shot [run](../glossary_EN.md#term-run) entrypoint that binds freeze
   verification, lease claim, and backend invocation in one process.

Freezing only the generic wrapper would leave the actual computational
semantics outside the immutable boundary. This slice records that blocker
explicitly instead of treating interface availability as execution readiness.

## Decision

Add the pure
`stage3b_qwake_lc4_execution_freeze.py` module. It:

- reverifies the frozen admission and exact implementation identities;
- binds the merge commit, PR head, Torch2PC, output and lease paths, cell
  counts, reserve probes, and lane order;
- builds deterministic request
  `stage3b-qwake-lc4-e-execution-freeze-request-v1`;
- requires claim and execution in the same process;
- requires no retry after claim, atomic result promotion, and a canonical
  backend receipt;
- records that the concrete backend, entrypoint, and immutable image are absent;
- rejects an existing repository lease or output root.

The module imports no Torch, exposes no CLI, invokes no executor, and writes
nothing to the repository. Its verifier round-trips the canonical request only
inside a temporary directory.

## Why the execution freeze is not materialized

The generic `RuntimeExecutionBackend` protocol defines call shape but does not
obtain the registered [runtime](../glossary_EN.md#term-runtime) frontier. The existing `RuntimeFrontierAdapter`
can capture already supplied state, but it does not construct the model,
engineering batch, or intermediate FixedPred states. A concrete backend must
therefore be implemented as a separate verifiable source slice.

Until then, the project cannot honestly freeze:

- the exact backend source digest;
- the only permitted entrypoint;
- an immutable image containing that backend;
- a static preflight from admission through complete output.

The next post-merge slice is `QW-LC4-E-runtime-backend-implementation`.

## Exact identities

```text
base_commit=24966cd2a0380e46ab1924ff4ab8987f17e1fe9e
base_parent_1=e0455dc77b49f5b220231509fe6062d275b6ee9b
implementation_head_commit=15588616c24d523f1c983fc205aeaae32a33958e
merged_at_utc=2026-07-28T01:24:32Z
torch2pc_commit=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
execution_freeze_request_sha256=sha256:9b28943043082efe96fb313f94875ef18c7f8e7361d8c0eb1b8c140e82a1e312
module_sha256=sha256:91466f1f95edfe91684ddc166af2b234bc95c678b6f5b7e8ed0c5aa8dd2a70a4
validator_sha256=sha256:2f2325e504b7dd7325ebb7802f5d69bc10491906a9aa8e79417b7dcbb04cf404
test_sha256=sha256:ace63e065e3d28bc28e9f40c3af5a15a95537f620702147b24180add924df2ac
authoring_json_sha256=sha256:9dfe3177442abdbe255047732a33d02d0987e4d634f0b1c629e1671fc68677dd
authoring_registry_sha256=sha256:9b65ba87c817fa67670ab4e225f15e9b1f2544459439cda2e5e0b621b324ca53
```

## Current boundaries

```text
LEASE_WRAPPER_IMPLEMENTATION_MERGED=true
EXECUTION_FREEZE_BRANCH_OPEN=true
EXECUTION_FREEZE_CONTRACT_MATERIALIZED=true
CONCRETE_RUNTIME_BACKEND_PRESENT=false
ONE_SHOT_ENTRYPOINT_PRESENT=false
IMMUTABLE_EXECUTION_IMAGE_PRESENT=false
EXECUTION_FREEZE_MATERIALIZED=false
EXECUTION_LEASE_MATERIALIZED=false
QW_LC4_E_EXECUTION_PERMITTED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

Merging this authoring slice permits only implementation of the concrete
backend and one-shot entrypoint. It does not permit a lease claim, an attempt, [dataset](../glossary_EN.md#term-dataset) access, production of
[evidence](../glossary_EN.md#term-evidence), or publication. The backend must
then be frozen by exact commit and image before a separate explicit invocation
can be authorized.

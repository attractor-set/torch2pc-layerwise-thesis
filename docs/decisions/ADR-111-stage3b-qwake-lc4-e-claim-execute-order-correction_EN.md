# ADR-111: immutable QW-LC4-E claim/execute ordering correction

- **Status:** accepted for the sole corrective PR; the corrected image and [attempt](../glossary_EN.md#term-attempt) 002 are not yet materialized
- **Date:** 2026-08-04
- **Scope:** `QW-LC4-E`

## Context

Attempt `qwake-lc4-runtime-validation-v1-attempt-001` ended with terminal class `nonzero_return_code`, return code `1`, and one child spawn. The immutable host receipt has file SHA-256 `9004103dd1a54299a8e217422f7b2c36d47f4bca5b9a81dd8f36f99cd9b6cf66` and semantic SHA-256 `649c2a723049e703c3ae1232d18ea9fbde25c393ff4b1047bfb6c5154e608f8f`.

The defect is localized to the historical entrypoint. It atomically created `lease-v1` and then called `execute_authorized_runtime`, which rechecked the pre-claim condition that the lease must be absent. That check correctly rejected the lease that had just been created. The computational backend and engineering-output publication did not start.

The historical modules, packages, and receipts are already part of the frozen [evidence](../glossary_EN.md#term-evidence) chain. Retroactive modification or digest rewriting is forbidden.

## Decision

The correction is an independent immutable overlay for a future corrected image. The historical `scripts/run_stage3b_qwake_lc4_authorized_runtime.py` remains byte-exact. The correction package contains a verified replacement and its exact unified patch.

The corrected entrypoint performs this order:

1. verify the materialized [execution](../glossary_EN.md#term-execution) freeze;
2. verify the operator acknowledgement;
3. obtain one `FrozenAdmissionIdentity` before claim;
4. construct the backend before the irreversible claim;
5. build the prospective lease from that admission;
6. atomically materialize the lease with the same admission;
7. pass the same admission to `run_claimed_execution_wrapper`.

After claim, calls to `verify_unconsumed_frozen_admission`, `claim_execution_lease`, or `execute_authorized_runtime` are forbidden. Existing wrapper code continues to provide atomic claim, no overwrite, materialized-lease revalidation, and no-replace output promotion.

## Sole-PR boundary

The correction is developed on one branch and one PR. The current commit authorizes only the correction overlay and its verification. It does not build an image, create attempt 002, or permit [execution](../glossary_EN.md#term-execution). Later commits in the same PR must add the exact corrected-image identity, a distinct attempt 002, and its new one-shot authorization. A second corrective PR is not permitted.

## Attempt-001 immutability

The following objects remain unchanged:

- `attempt-001.execution-lease.json`;
- `attempt-001.execution-lease-v2.json`;
- `attempt-001.host-outcome.json`.

Attempt 001 is terminal. Automatic or manual retry under its identity is forbidden.

## Consequences

- historical frozen source identities remain valid;
- the correction is verifiable before image construction;
- one admission identity is carried through build, materialize, and execute;
- another [runtime](../glossary_EN.md#term-runtime) launch is possible only as attempt 002 after a separate admission in the same PR;
- `QW-5`, scientific data collection, and publication remain closed.

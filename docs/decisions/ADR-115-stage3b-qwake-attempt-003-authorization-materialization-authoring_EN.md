# ADR-115: attempt-003 authorization materialization authoring

## Status

Accepted as a bounded authoring of the future authorization-issuance mechanism.

## Context

After PR #183 merged, `main` commit
`8e1754d1859796bc809c27c078e7b0b180a685ba` contains the verified [attempt](../glossary_EN.md#term-attempt)-003
[execution](../glossary_EN.md#term-execution) freeze with canonical identity
`sha256:82e7509a0d2627f8b91daa34049307da573619b740a2022b72b922edcd07898e`.
The attempt-003 authorization is absent, no lease or outcome exists, and the
[runtime](../glossary_EN.md#term-runtime) has not started.

The frozen `Attempt003Authorization` already defines the final
`authorization.json` schema. In particular, a valid record immediately has
status `effective_unconsumed_attempt_003_runtime_authorization` and
`authorization_effective=true`. Adding an intermediate post-merge-verified
field would require changing the frozen
`stage3b_qwake_attempt_003_contract.py` and would invalidate the execution
freeze. This ADR therefore does not modify the runtime contract.

## Decision

Add a separate pure file materializer for future authorization issuance, a
verifier, and negative tests. This slice creates only the future capability
and **does not create** the canonical
`stage3b-qwake-attempt-003-authorization-v1` package.

Future issuance is a distinct operator operation. The materializer must:

1. reverify the existing attempt-003 execution freeze first;
2. require absence of the canonical authorization, both leases, durable
   outcome, output root, and attempt staging tree;
3. verify exact SHA-256 identities of immutable authorization inputs;
4. require the exact action phrase
   `AUTHORIZE_QWAKE_LC4_ATTEMPT_003_ONE_SHOT_ENGINEERING_INVOCATION`;
5. bind `operator_identity` to the current local POSIX account;
6. construct the existing `Attempt003Authorization` with
   `execution_count=1`, unconsumed authorization, unstarted attempt, and no
   retry permission;
7. create exactly `authorization.json`, `source-SHA256SUMS`, and
   `SHA256SUMS` in a sibling staging directory, verify them, and atomically
   rename the directory with replacement forbidden;
8. invoke the existing unconsumed-authorization verification after promotion.

The future authorization source registry binds only inputs that are already
frozen: the three execution-freeze files, scientific authorization, and four
runtime components. Mutable test infrastructure, especially
`tests/conftest.py`, is deliberately excluded.

## Boundary

This slice does not materialize the real authorization, consume it, create a
lease or outcome, build or run Docker, invoke [runtime](../glossary_EN.md#term-runtime)
or model code, or access a [dataset](../glossary_EN.md#term-dataset).

The existence of the materializer is not permission to invoke it against the
production repository. Actual creation of
`experiments/frozen/stage3b-qwake-attempt-003-authorization-v1` requires a
separate explicit authorization after this authoring slice is merged and
independently verified.

## Consequence

After this slice is merged and post-merge verified, the only next admissible
step is a separately authorized one-shot authorization issuance. Attempt
execution remains a distinct later operation and is not permitted merely by
the existence of an authorization record.

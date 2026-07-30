# ADR-082: `QW-LC4-E` runtime-operation identity repair

[Русская версия](ADR-082-stage3b-qwake-lc4-e-runtime-operation-identity-repair.md)

- **Status:** accepted as identity-repair authoring; [execution](../glossary_EN.md#term-execution) is blocked
- **Date:** 29 July 2026
- **Base commit:** `97dacb207aa201f1fd2f43c66ae34b1adced32bb`

## Context

After the one-line Ruff `UP038` correction, the actual ADR-081 module no
longer matched the SHA-256 recorded by the historical ADR. PR #142 correctly
merged the corrected source tree, but the original two-file
`runtime-operation-v1` package bound only `operation.json` and therefore could
not detect drift of the executable module itself.

The historical ADR-081 and `runtime-operation-v1` package must not be
rewritten. A separate non-retroactive repair record is required to bind the
actual module, verifier, tests, and both ADR language versions to the exact PR
#142 merge commit.

## Decision

1. Preserve ADR-081 and its two-file frozen package unchanged as the historical
   authoring artifact.
2. Add the
   `stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation-identity-repair-v1`
   package containing `repair.json`, `source-SHA256SUMS`, and `SHA256SUMS`.
3. Bind the source registry to the corrected [runtime](../glossary_EN.md#term-runtime)-operation module, the
   existing verifier and test, ADR-081 RU/EN, ADR-082 RU/EN, and the repair's
   own module/verifier/test.
4. Require `verify_engineering_invocation_runtime_operation` to complete the
   effect-free identity-repair verification exactly once.
5. Reject the stale module SHA as an active identity while retaining it only as
   an explicitly marked historical defect.
6. Keep execution closed: a corrected full-validation receipt, repair merge,
   persistent lease v2, and durable negative host outcome remain separate
   mandatory gates.

## Identities

```text
runtime_operation_head_commit=423684f3e8eaad1858161503d63d514a5eeb9e5e
runtime_operation_merge_commit=97dacb207aa201f1fd2f43c66ae34b1adced32bb
runtime_operation_merged_at_utc=2026-07-30T00:31:26Z
historical_runtime_operation_sha256=sha256:0332428014f7f8385c789ba7e7c55d6c2ec03b020e3f83df9ac9714483bb6bf8
stale_module_sha256=sha256:eb337b1f9cd1c95570d7ec22160886a43efe2531c9c5131b7ac29a84123115a4
corrected_module_sha256=sha256:da08c66e78340c067e391a28f326f0d9bb7465d4a56073deac458a764ae6b30d
runtime_operation_verifier_sha256=sha256:78fe6cee7af7f3d652a5b16c1d095540a47dd12177d253c1f8d37da0c812fbc4
runtime_operation_test_sha256=sha256:76ede6b6f004d9ddab0bca2fb8891bf3d69d7355665e8fb729f2cf3c0c651ee5
historical_adr_ru_sha256=sha256:eb16141e0fe86f80075c6753512f3b4bda5a5244598b81874af4d4eed42946da
historical_adr_en_sha256=sha256:b4d17e5d2d9c11c2ca75876331eca845637f3cb7f1cc00ea8897465cbe959370
identity_repair_sha256=sha256:ff6d22e98257bb55774abf8ad2418a60c759981049994720ae814e9ff6ccc4c6
```

## Boundaries

```text
HISTORICAL_RUNTIME_OPERATION_PACKAGE_PRESERVED=true
CORRECTED_MODULE_IDENTITY_FROZEN=true
RUNTIME_OPERATION_SELF_IDENTITY_VERIFIED=true
CORRECTED_FULL_VALIDATION_RECEIPT_PRESENT=false
RUNTIME_OPERATION_IDENTITY_REPAIR_MERGED=false
LATEST_AUTHORIZATION_BOUND_IN_PERSISTENT_LEASE=false
DURABLE_NEGATIVE_HOST_OUTCOME_DEFINED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

The corrected source identity is now checked against the actual tree, and any
change to the runtime-operation module, verifier, tests, or bound ADRs fails
closed. After commit/PR/merge/post-merge verification, the next admissible
slice is persistent [evidence](../glossary_EN.md#term-evidence) chain v2. The execution request and one-shot run
remain prohibited before that point.

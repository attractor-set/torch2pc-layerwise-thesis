# ADR-123: `QW-5` single scientific-image freeze

[Russian version](ADR-123-stage3b-qwake-qw5-single-scientific-image-freeze.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-fp-scientific-image-freeze-corrective-v1/freeze.json -->

Normative terms:
[attempt](../glossary_EN.md#term-attempt),
[execution](../glossary_EN.md#term-execution),
[run](../glossary_EN.md#term-run),
[runtime](../glossary_EN.md#term-runtime),
[evidence](../glossary_EN.md#term-evidence),
[freeze](../glossary_EN.md#term-freeze),
[candidate](../glossary_EN.md#term-candidate),
[test-dataset access](../glossary_EN.md#term-test-dataset-access), and
[dataset](../glossary_EN.md#term-dataset).

## Status

Accepted as the materialized and independently verified corrective `QW-5`
single scientific-image freeze. This decision starts no scientific campaign.

## Historical boundary

`Attempt-001` crossed the effect boundary and successfully built the image once,
but the original static-validation procedure failed before `freeze.json` was
materialized. `Attempt-001` therefore remains a terminal unsuccessful attempt:
it was not retried, rewritten, or reinterpreted as PASS.

The surviving immutable
[candidate](../glossary_EN.md#term-candidate)
`sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3` was later evaluated by a separate corrective-validation
procedure. The full suite reported `1659 passed, 8 skipped`; dependency
checking, byte-for-byte executable-source verification, and the dataset-payload
absence audit passed. That evidence was durably materialized and independently
verified, then separately adjudicated and independently verified again.

## Decision

1. The sole scientific image for `C1/C2/C3/R` is
   `sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3`.
2. The image is bound to source commit `4eb23b6f5e2e3b2f3cdee83a4732f8a091b7b662` / tree `1db3999089bf15d153a0a83920f6c1e9a1431218` and
   immutable ROCm base RepoDigest `rocm/pytorch@sha256:96a2fb24dec9896e2f8238178f0c49d0dcc4c7dcc597be09e4564316bd86d191`.
3. The corrective freeze semantic hash is
   `sha256:b435c09c02783f09156cfb7f68045151aa659e144e3c95d85480cee99020f6f4`.
4. `Attempt-001` remains `terminal`, `success=false`,
   `reinterpreted=false`, and `retry_performed=false`.
5. The original QW-5 driver was not replayed and missing original
   static-validation artifacts were not synthesized.
6. Executable/dependency source does not change after the freeze.
7. The same image digest is mandatory for `C1_COLLECTION`,
   `C2_CALIBRATION`, `C3_CONFIRMATORY`, and `R_REPLICATION`.
8. `QW-5` does not open C1. The next separate boundary is a frozen C1 request
   and authorization bound to this corrective freeze.
9. Test-dataset access, scientific execution, and publication remain closed.

## Verifiable boundary

```text
QW_LC4_E_COMPLETE=true
QW5_IMAGE_FROZEN=true
QW5_FREEZE_MODE=corrective_evidence
QW5_IMAGE_DIGEST=sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3
QW5_SOURCE_COMMIT=4eb23b6f5e2e3b2f3cdee83a4732f8a091b7b662
QW5_SOURCE_TREE=1db3999089bf15d153a0a83920f6c1e9a1431218
QW5_CORRECTIVE_FREEZE_SHA256=sha256:b435c09c02783f09156cfb7f68045151aa659e144e3c95d85480cee99020f6f4
ATTEMPT001_TERMINAL=true
ATTEMPT001_SUCCESS=false
ATTEMPT001_REINTERPRETED=false
ATTEMPT001_RETRY_PERFORMED=false
EXECUTION_IMAGE_STRATEGY=single_immutable_superset_image
SAME_IMAGE_DIGEST_REQUIRED_ACROSS_C1_C2_C3_R=true
EXECUTABLE_CODE_CHANGES_AFTER_IMAGE_FREEZE=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=C1-request-freeze-and-authorization
```

Evidence chain:
- corrective validation receipt: `sha256:7ee321d1feeda213828c67151e08ccb470d8ab52cf088ad6bff8e10269cc10e2`;
- corrective validation log: `sha256:86a2b8e662f519fc28fbe292f36b1997a9f956aa18f69c3ce1ed7383749d2bd7`;
- corrective adjudication: `sha256:e345db724703607cc4d22c4428d480c6eec6820f31be657eb6a86ac7f556dea1`;
- corrective freeze authorization: `sha256:505b995dba38da25bf2724a043166cb3f3c85e5a43c34370084a3f62582b0ba3`;
- corrective freeze: `sha256:b435c09c02783f09156cfb7f68045151aa659e144e3c95d85480cee99020f6f4`.

# ADR-125: superseding `QW-5` scientific-image freeze

[Russian version](ADR-125-stage3b-qwake-qw5-superseding-scientific-image-freeze.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-qw5-superseding-scientific-image-freeze-v1/repository-integration.json -->

Normative terms:
[execution](../glossary_EN.md#term-execution),
[runtime](../glossary_EN.md#term-runtime),
[evidence](../glossary_EN.md#term-evidence),
[freeze](../glossary_EN.md#term-freeze),
[candidate](../glossary_EN.md#term-candidate),
[campaign role](../glossary_EN.md#term-campaign-role),
[dataset](../glossary_EN.md#term-dataset), and
[test-dataset access](../glossary_EN.md#term-test-dataset-access).

## Status

Accepted as repository integration of the already built, validated, frozen, and
independently verified superseding `QW-5` scientific image. This slice neither
builds nor runs a Docker image and does not open a scientific campaign.

## Historical boundary

ADR-123 and the version-1 image
`sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3` remain an immutable historical freeze.
They are neither removed nor reinterpreted. ADR-124 established that version 1
does not contain the preregistered scientific-campaign entrypoint required for
future C1, so a superseding image was required.

The superseding image was built exactly once from canonical merged source
`95a0bf35c87f87ee836596c02ab90a71703714f3` / `e0fdaa3214f4a39b92e82e2d2529c6c506513166`, passed the 157-path runtime-closure
validation and the `45 passed` targeted suite, then was frozen and independently
verified without a rebuild.

## Decision

1. For all **future** `C1_COLLECTION`, `C2_CALIBRATION`,
   `C3_CONFIRMATORY`, and `R_REPLICATION`, the sole admissible scientific image
   is `sha256:7aefbc241ad725f4ac31d8b72c63a82247516ad4831aad6f7d0ef89817f9dacb`.
2. Its semantic freeze hash is `sha256:47c20698ac57c1b50f4bbe0314649b0d07494ecc1199b32819ecde7b684d9904`.
3. The image is bound to source commit `95a0bf35c87f87ee836596c02ab90a71703714f3`, source tree `e0fdaa3214f4a39b92e82e2d2529c6c506513166`,
   runtime manifest `sha256:d6e3bdf33b868334062dd6e12e958392a61f8101b5f0410353f39f20338d6c3d`, and implementation
   `sha256:2047bf5ba1c2555dcea54efd3381ef35c16411ba7efbe84a75116858187708fa`.
4. ADR-125 supersedes ADR-123's operational image decision for future campaigns
   without altering the historical facts, bytes, or status of QW-5 v1.
5. The original evidence package is copied into the repository byte-for-byte and
   its internal `SHA256SUMS` remains unchanged. The repository wrapper also binds
   the independent verification and this integration authorization.
6. The same superseding image digest is mandatory across `C1/C2/C3/R`.
7. This decision does not open C1. The next separate boundary is C1 request
   freeze and execution authorization bound to this freeze.
8. Scientific execution, test-dataset access, and publication remain closed.

## Verifiable boundary

```text
QW5_V1_HISTORICAL_FREEZE_PRESERVED=true
QW5_V1_IMAGE_DIGEST=sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3
QW5_V1_CORRECTIVE_FREEZE_SHA256=sha256:b435c09c02783f09156cfb7f68045151aa659e144e3c95d85480cee99020f6f4
SUPERSEDING_QW5_IMAGE_DIGEST=sha256:7aefbc241ad725f4ac31d8b72c63a82247516ad4831aad6f7d0ef89817f9dacb
SUPERSEDING_QW5_FREEZE_SHA256=sha256:47c20698ac57c1b50f4bbe0314649b0d07494ecc1199b32819ecde7b684d9904
SUPERSEDING_QW5_SOURCE_COMMIT=95a0bf35c87f87ee836596c02ab90a71703714f3
SUPERSEDING_QW5_SOURCE_TREE=e0fdaa3214f4a39b92e82e2d2529c6c506513166
RUNTIME_SOURCE_MANIFEST_SHA256=sha256:d6e3bdf33b868334062dd6e12e958392a61f8101b5f0410353f39f20338d6c3d
ORCHESTRATOR_IMPLEMENTATION_SHA256=sha256:2047bf5ba1c2555dcea54efd3381ef35c16411ba7efbe84a75116858187708fa
SUPERSEDING_IMAGE_FREEZE_INDEPENDENTLY_VERIFIED=true
ORIGINAL_EVIDENCE_BYTES_PRESERVED=true
SAME_IMAGE_DIGEST_REQUIRED_ACROSS_C1_C2_C3_R=true
C1_REQUEST_FROZEN=false
C1_EXECUTION_AUTHORIZATION_ISSUED=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=merge-post-merge-verify-then-C1-request-freeze-and-authorization
```

Repository integration hash:
`sha256:e35d1c90c3dc118c3a1514a62c7487196c48482de4cb1aae74e9ba942b2b518c`.

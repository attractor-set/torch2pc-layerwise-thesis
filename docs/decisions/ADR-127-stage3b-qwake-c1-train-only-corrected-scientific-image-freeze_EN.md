# ADR-127: repository integration of the corrected `C1` scientific image

[Русская версия](ADR-127-stage3b-qwake-c1-train-only-corrected-scientific-image-freeze.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-c1-train-only-corrected-scientific-image-freeze-v1/repository-integration.json -->

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
independently verified corrected scientific image that removes the ADR-126 C1
dependency on the broader dataset-constructor surface. This slice does not
build or run a Docker image, freeze the C1 request, or open a scientific
campaign.

## Historical boundary

ADR-123 and QW-5 v1 image `sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3` remain an immutable
historical freeze. ADR-125 and image `sha256:7aefbc241ad725f4ac31d8b72c63a82247516ad4831aad6f7d0ef89817f9dacb` also remain
unchanged: they document the correctly built superseding orchestrator image,
while ADR-126 established that this image cannot be treated as C1-admissible
because test-resource isolation in the data path was not narrow enough.

ADR-126 was merged as `3858d3a7e6d7b3401e999523bc6675dc7dd0223d` / `f516667472e1ea2a8e2826f520c055cfe2dd0351` and moved isolation under
project control: a request can bind only the exact train-only IDX pair and the
scientific runtime no longer uses a torchvision Dataset constructor.

Corrected image `sha256:89703b0b37b2729855835a6ed19ba1ca397ae14614c318344bd7625d12c727ef` was built exactly once from that
state, passed the 157-path runtime-closure check, a dedicated `5 passed`
train-only isolation validation, the existing `45 passed` targeted validation,
`pip check`, and dataset-payload absence. It was then frozen as
`sha256:ce8c054c92df18512b2a88ac25148f44c15487d8c2d4e68d8751966ac17bf287` and independently verified without `docker run` or
a rebuild.

## Decision

1. After this integration is merged and independently post-merge verified,
   `sha256:89703b0b37b2729855835a6ed19ba1ca397ae14614c318344bd7625d12c727ef` becomes the sole operational scientific image for
   future `C1_COLLECTION`, `C2_CALIBRATION`, `C3_CONFIRMATORY`, and
   `R_REPLICATION`.
2. The image is bound to source commit `3858d3a7e6d7b3401e999523bc6675dc7dd0223d`, tree `f516667472e1ea2a8e2826f520c055cfe2dd0351`,
   runtime manifest `sha256:01d86f045bf42554382654d2c48f2be23f4763b6fbdc4aa1c9e7cff939367561`, and corrected
   implementation `sha256:94cb8b210dcde5b4b2a71ed85c60938eb748727af9ef0a8d1bdb958b4739c4f4`.
3. ADR-127 supersedes ADR-125's operational-image decision for future campaigns
   without changing the historical facts, bytes, or status of ADR-123, ADR-125,
   or their images.
4. The original 18 evidence files are copied into the repository byte-for-byte.
   Their original `SHA256SUMS`, whose hash is `sha256:8854315bc989b1d62feda4fca07a6a0b5ee5bbd529a322f6579cd199ce0a0271`, remains
   unchanged; the repository wrapper additionally binds the integration
   authorization and a fresh independent verification.
5. The same corrected image digest is mandatory across `C1/C2/C3/R`.
6. The previously issued C1 request-freeze authorization remains unconsumed.
   This slice does not use it. Returning to that boundary is permitted only
   after ADR-127 is merged and separately post-merge verified.
7. This decision does not execute C1. C1 execution authorization remains a
   separate later boundary.
8. Scientific execution, test-dataset access, and publication remain closed.

## Verifiable boundary

```text
QW5_V1_HISTORICAL_FREEZE_PRESERVED=true
PREVIOUS_SUPERSEDING_IMAGE_PRESERVED=true
PREVIOUS_SUPERSEDING_IMAGE_DIGEST=sha256:7aefbc241ad725f4ac31d8b72c63a82247516ad4831aad6f7d0ef89817f9dacb
PREVIOUS_SUPERSEDING_IMAGE_C1_ADMISSIBLE=false
CORRECTED_SCIENTIFIC_IMAGE_DIGEST=sha256:89703b0b37b2729855835a6ed19ba1ca397ae14614c318344bd7625d12c727ef
CORRECTED_SCIENTIFIC_IMAGE_FREEZE_SHA256=sha256:ce8c054c92df18512b2a88ac25148f44c15487d8c2d4e68d8751966ac17bf287
CORRECTED_SCIENTIFIC_IMAGE_FREEZE_INDEPENDENTLY_VERIFIED=true
TRAIN_ONLY_ISOLATION_VALIDATED=true
RUNTIME_SOURCE_MANIFEST_SHA256=sha256:01d86f045bf42554382654d2c48f2be23f4763b6fbdc4aa1c9e7cff939367561
CORRECTION_IMPLEMENTATION_SHA256=sha256:94cb8b210dcde5b4b2a71ed85c60938eb748727af9ef0a8d1bdb958b4739c4f4
ORIGINAL_EVIDENCE_BYTES_PRESERVED=true
ORIGINAL_EVIDENCE_FILE_COUNT=18
SAME_IMAGE_DIGEST_REQUIRED_ACROSS_C1_C2_C3_R=true
C1_REQUEST_FREEZE_AUTHORIZATION_PREVIOUSLY_ISSUED=true
C1_REQUEST_FREEZE_AUTHORIZATION_CONSUMED=false
C1_REQUEST_FREEZE_PERMITTED=false
C1_REQUEST_FROZEN=false
C1_EXECUTION_AUTHORIZATION_ISSUED=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=merge-post-merge-verify-then-resume-existing-C1-request-freeze-boundary
```

Repository integration hash: `sha256:70012413e1d6bd69dbad060cef0d4b19e0bfe2635eca4dbe746ccfc42544ae72`.

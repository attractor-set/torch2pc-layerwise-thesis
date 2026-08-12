# ADR-126: C1 train-only dataset isolation correction

[Russian version](ADR-126-stage3b-qwake-c1-train-only-dataset-isolation-correction.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-c1-train-only-dataset-isolation-correction-v1/implementation.json -->

Normative terms:
[execution](../glossary_EN.md#term-execution),
[runtime](../glossary_EN.md#term-runtime),
[evidence](../glossary_EN.md#term-evidence),
[freeze](../glossary_EN.md#term-freeze),
[campaign role](../glossary_EN.md#term-campaign-role),
[dataset](../glossary_EN.md#term-dataset), and
[test-dataset access](../glossary_EN.md#term-test-dataset-access).

## Status

Accepted as source authoring for the minimal train-only data-path correction required
before a C1 request may be frozen. This slice does not build or run an image,
freeze a C1 request, issue C1 execution authorization, execute science, access
test data, or permit publication.

## Admission finding

After ADR-125 and PR #197 were merged and independently verified at
`2d748751482a6b3ecb200fb3816d41f48d8ed8cc` /
`f6ce596c2d7ff45a054ed8c0bb5d6ceb3cc3b97d`, the C1 request-freeze admission
audit remained fail-closed. The project runtime delegated live train-data
construction to the torchvision MNIST-family dataset constructor before
train-only materialization. Because `test_dataset_access=false` means test data
must not be read, C1 isolation could not be proven from the project-owned
execution path. The prior C1 request-freeze authorization remains issued but
unconsumed.

## Decision

1. Preserve image `sha256:7aefbc241ad725f4ac31d8b72c63a82247516ad4831aad6f7d0ef89817f9dacb` and freeze
   `sha256:47c20698ac57c1b50f4bbe0314649b0d07494ecc1199b32819ecde7b684d9904`
   unchanged as historical evidence. Do not reinterpret that image as C1-ready.
2. Restrict `ScientificDatasetBinding` to exactly two canonical uncompressed
   train assets: `train-images-idx3-ubyte` followed by
   `train-labels-idx1-ubyte` under `data/<dataset-name>/raw/`. A `t10k-*` asset,
   compressed alternative, missing asset, extra asset, or reordered pair is not
   a valid scientific request.
3. Remove the torchvision dataset-constructor surface from the scientific
   runtime. Parse only the two already hash-verified bound IDX files. Require
   image magic 2051, label magic 2049, 28x28 geometry, exact payload lengths,
   and equal image/label cardinality.
4. Preserve the previous image transform semantics explicitly: convert uint8 to
   float32 by division by 255 and zero-pad two pixels on every side, yielding
   `1x32x32`.
5. Add an adversarial test with real `t10k-*` trap files present. Any opening of
   a test resource fails the test. Add negative request-schema and malformed
   IDX tests.
6. Do not mutate the historical orchestrator runtime manifest. Materialize a new
   prospective 157-path runtime closure at
   `experiments/frozen/stage3b-qwake-c1-train-only-dataset-isolation-correction-v1/runtime-SHA256SUMS`, digest `sha256:01d86f045bf42554382654d2c48f2be23f4763b6fbdc4aa1c9e7cff939367561`.
7. Do not build an image in this slice. After merge and independent post-merge
   verification, a separate authorization is required to build, validate, and
   freeze the corrected image. Only that future freeze may return the workflow
   to the already-issued C1 request-freeze boundary.

## Verifiable boundary

```text
C1_ADMISSION_AUDIT_V1_SHA256=sha256:119113ab83b2622ab0e005bc16318bf88fc4e41ced56ad183c10813d5e63f784
C1_TRAIN_ONLY_DATASET_ISOLATION_CORRECTION_AUTHORED=true
REQUEST_SCHEMA_EXACT_TRAIN_ASSET_COUNT=2
REQUEST_SCHEMA_TEST_RESOURCE_BINDING_PERMITTED=false
TORCHVISION_DATASET_CONSTRUCTOR_IN_SCIENTIFIC_RUNTIME=false
TRAIN_ONLY_IDX_PARSER=true
ADVERSARIAL_T10K_OPEN_TRAP_TEST=true
RUNTIME_SOURCE_PATH_COUNT=157
RUNTIME_SOURCE_MANIFEST_SHA256=sha256:01d86f045bf42554382654d2c48f2be23f4763b6fbdc4aa1c9e7cff939367561
CURRENT_SUPERSEDING_IMAGE_PRESERVED=true
CURRENT_SUPERSEDING_IMAGE_C1_ADMISSIBLE=false
NEW_SCIENTIFIC_IMAGE_REQUIRED=true
NEW_SCIENTIFIC_IMAGE_BUILT=false
C1_REQUEST_FREEZE_AUTHORIZATION_CONSUMED=false
C1_REQUEST_FROZEN=false
C1_EXECUTION_AUTHORIZATION_ISSUED=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=merge-post-merge-verify-then-corrected-image-build-validation-freeze
```

Implementation self-hash: `sha256:85ae69d5f39b898e1645e5088d67ad39378484d1a7506e92ae08d4d8d9f2033b`.

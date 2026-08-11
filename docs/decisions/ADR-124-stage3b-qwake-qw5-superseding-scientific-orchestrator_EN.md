# ADR-124: superseding `QW-5` scientific orchestrator

[Russian version](ADR-124-stage3b-qwake-qw5-superseding-scientific-orchestrator.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-scientific-orchestrator-v1/implementation.json -->

Normative terms:
[execution](../glossary_EN.md#term-execution),
[runtime](../glossary_EN.md#term-runtime),
[evidence](../glossary_EN.md#term-evidence),
[exact-implementation freeze](../glossary_EN.md#term-exact-implementation-freeze),
[capability gate](../glossary_EN.md#term-capability-gate),
[campaign role](../glossary_EN.md#term-campaign-role),
[architecture](../glossary_EN.md#term-architecture),
[QWake-FP](../glossary_EN.md#term-qwake-fp),
[dataset](../glossary_EN.md#term-dataset), and
[test-dataset access](../glossary_EN.md#term-test-dataset-access).

## Status

Accepted as source authoring for a superseding scientific orchestrator after
structural C1-readiness verification. This slice does not build a new image,
replace the previously frozen `QW-5` image, or open a scientific campaign.

## Rationale

After ADR-123 merged, an independent structural audit of source tree
`4eb23b6f5e2e3b2f3cdee83a4732f8a091b7b662` identified an executable-surface
limitation. The capability model contains role `C1_COLLECTION`, `A0/A1/A2`
components, registered analytics, canonical suffix completion, and post-action
oracle labels. The only ready QWake-FP executable chain, however, is an
engineering-validation path using `synthetic-engineering-batch-v1` and
materializing `SCIENTIFIC_EVIDENCE=false`. ADR-123 contains no preregistered
scientific-campaign entrypoint.

A C1 request therefore cannot be soundly bound to image
`sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3`.
Changing that image or its source tree after freeze is forbidden; ADR-123 is
preserved as the historically correct QW-5 version-1 freeze.

## Decision

1. Preserve the ADR-123 image and corrective freeze
   `sha256:b435c09c02783f09156cfb7f68045151aa659e144e3c95d85480cee99020f6f4`
   unchanged and do not reinterpret them as C1 readiness.
2. Add one generic preregistered orchestrator for `C1_COLLECTION`,
   `C2_CALIBRATION`, `C3_CONFIRMATORY`, and `R_REPLICATION` rather than creating
   a separate executable path for every stage.
3. Split orchestration into two preregistered halves. The host half verifies the
   exact image and source commit, atomically consumes the one-shot authorization
   through `host-claim.json`, and performs at most one `docker run`. The embedded
   half re-verifies request, authorization, image identity, source manifest, and
   predecessor receipts, then executes only the closed component registry.
4. Forbid arbitrary executable code, shell commands, source-overlay mounts,
   container networking, automatic retry, test-dataset access, and publication.
5. For live stages permit only the registered split and exact file hashes;
   `C2_CALIBRATION` remains completely offline with respect to live data.
6. Bind predecessor receipts by both semantic self-hash and file-byte hash. For
   `C2/C3/R`, additionally verify that each receipt names the exact sealed
   trajectory dataset or frozen policy bound by the request.
7. Extend only the pure QWake-FP feature schema so registered `A1/A2`
   observations may contain canonical tuples and mappings. Numeric policy
   thresholds remain valid only for preregistered scalar fields.
8. Do not modify `stage3b_qwake_lc4_bounded.py`. The `float32` canonicalization
   required for the redundant error field occurs only in the new layer before
   invoking the existing analytic-completion primitive; comparison profile
   `rocm_float32_canonical` and its tolerances do not change.
9. Seal the future image executable closure in `runtime-SHA256SUMS`. A scientific
   campaign request must bind the exact hash of this manifest.
10. Do not build or run the superseding image in this slice. After merge, perform
    a separate post-merge verification, then separately build, validate, and
    freeze the new image. Only after that freeze may a C1 request be frozen.

## Verifiable boundary

```text
QW5_V1_PRESERVED=true
QW5_V1_IMAGE_DIGEST=sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3
QW5_V1_CORRECTIVE_FREEZE_SHA256=sha256:b435c09c02783f09156cfb7f68045151aa659e144e3c95d85480cee99020f6f4
C1_READINESS_AUDIT_V3_SHA256=sha256:c521e6992d5d9dbf2e0c8acdde4482d1b0ead82b1b4d8af0fcd1d2b3d0e1b5e2
C1_PREREGISTERED_SCIENTIFIC_CAMPAIGN_ENTRYPOINT_IN_V1=false
SUPERSEDING_ORCHESTRATOR_AUTHORED=true
SUPERSEDING_ORCHESTRATOR_ARCHITECTURE=fixed_host_launcher_plus_embedded_closed_registry_runner
ARBITRARY_CODE_LOADING=false
SHELL_COMMAND_LOADING=false
SOURCE_OVERLAY_PERMITTED=false
AUTOMATIC_RETRY_PERMITTED=false
SUPERSEDING_QW5_IMAGE_BUILT=false
SUPERSEDING_QW5_IMAGE_FROZEN=false
C1_REQUEST_FROZEN=false
C1_EXECUTION_AUTHORIZATION_ISSUED=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=merge-post-merge-verify-then-superseding-image-build-and-freeze
```

## Consequences

ADR-123 remains an immutable historical version-1 freeze rather than a failed
scientific run. The new source establishes only the executable prerequisite for
a future superseding image. Until that image is separately validated and frozen,
the C1 request, scientific execution, test-dataset access, and publication stay
closed.

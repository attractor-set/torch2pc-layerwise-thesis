# ADR-131: repository integration of the new frozen `C1` request

[Русская версия](ADR-131-stage3b-qwake-c1-hostfix-request-freeze-repository-integration.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-c1-hostfix-image-bound-request-freeze-v1/repository-integration.json -->

Normative terms:
[attempt](../glossary_EN.md#term-attempt),
[execution](../glossary_EN.md#term-execution),
[evidence](../glossary_EN.md#term-evidence),
[freeze](../glossary_EN.md#term-freeze),
[campaign role](../glossary_EN.md#term-campaign-role),
[dataset](../glossary_EN.md#term-dataset), and
[test-dataset access](../glossary_EN.md#term-test-dataset-access).

## Status

Accepted as repository integration of the new `C1_COLLECTION` request already
frozen and independently verified after the host-identity correction and new
scientific-image freeze. This slice does not modify the request or
preregistration, refreeze it, or open `Attempt-002`.

## Bound chain

Canonical repository/evidence main: `4e8f293d209bdc1661f8fca9095e5c522673b559` / `d58d96865f35c1f387f9b3406380f238280cd7da`.
Executable source baked into the image: `98cff5b2ecd64e1c96e19f0b04104ac00a5c3cf2`.
Scientific image: `sha256:12a4a6792530471517e53b30625bcfc45031a97bb9072f54bfa0c966e3fc2b5d`.
Image freeze: `sha256:ea207e6d31507d449e24fc30bb74fb21ec6560b1ec4a777cb1199de3ad63184f`.
Image repository integration: `sha256:66369e9f6f666e94625f403c341028ae2249a7e74707c22b0fef75231b67fc46`.

Preregistration: `sha256:ed82a638b31761364f06fd460bec64bb668f6a9cb4bd077af53339dfd479048b`.
Request semantic identity: `sha256:af7c27ec0db83d907b51361a8bb726db51f41fdbdc6bc341156b420648c606fd`.
Request file identity: `sha256:41bdb53052e03476ba908bf1ee1cbda0cda231c06361fcb6031848d857e0f19b`.
Request freeze: `sha256:7fe57faefcc3aa92463e01422546e015e02e7a68c13dbbc9df1ef9feb7452b82`.

## Decision

1. The seven original request-freeze evidence files are copied byte-for-byte;
   the original `SHA256SUMS` with identity `sha256:fab9a28dcc6c47fa84b905740f64c09f3aaed2afd3a4cfbd78aa34c8fa8ae858` remains
   unchanged.
2. External evidence is an opaque byte-preserved surface. A package-scoped Git
   `binary` rule protects sealed `.log` bytes from EOL normalization.
3. The repository wrapper binds the evidence to integration authorization, an
   independent read-only verification, and integration hash
   `sha256:9bffb8d2bc2516d1075c2a4615c4140b18b2eb2cc9068bac7581a1c7ed001e8f`.
4. `request.json` and `preregistration-manifest.json` are neither modified nor
   recreated.
5. The previous C1 request remains historical and non-reusable.
6. The new request is frozen, but execution authorization is not issued and
   `ATTEMPT002_CREATED=false`.
7. Docker/image effects, scientific execution, test-dataset access, and
   publication remain closed.
8. After merge and separate post-merge verification, the next boundary may
   only be a separate C1 `Attempt-002` execution authorization.

## Verifiable boundary

```text
CANONICAL_REPOSITORY_MAIN=4e8f293d209bdc1661f8fca9095e5c522673b559
BAKED_IMAGE_SOURCE_COMMIT=98cff5b2ecd64e1c96e19f0b04104ac00a5c3cf2
IMAGE_DIGEST=sha256:12a4a6792530471517e53b30625bcfc45031a97bb9072f54bfa0c966e3fc2b5d
IMAGE_FREEZE_SHA256=sha256:ea207e6d31507d449e24fc30bb74fb21ec6560b1ec4a777cb1199de3ad63184f
C1_REQUEST_SHA256=sha256:af7c27ec0db83d907b51361a8bb726db51f41fdbdc6bc341156b420648c606fd
C1_REQUEST_FILE_SHA256=sha256:41bdb53052e03476ba908bf1ee1cbda0cda231c06361fcb6031848d857e0f19b
C1_REQUEST_FREEZE_SHA256=sha256:7fe57faefcc3aa92463e01422546e015e02e7a68c13dbbc9df1ef9feb7452b82
PREREGISTRATION_MANIFEST_SHA256=sha256:ed82a638b31761364f06fd460bec64bb668f6a9cb4bd077af53339dfd479048b
C1_REQUEST_FREEZE_INDEPENDENTLY_VERIFIED=true
ORIGINAL_EVIDENCE_BYTES_PRESERVED=true
ORIGINAL_EVIDENCE_FILE_COUNT=7
PREVIOUS_C1_REQUEST_REUSABLE=false
REQUEST_FREEZE_AUTHORIZATION_RECONSUMED=false
NEW_C1_REQUEST_FROZEN=true
NEW_C1_EXECUTION_AUTHORIZATION_ISSUED=false
ATTEMPT002_CREATED=false
C1_COLLECTION_OPEN=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=merge-post-merge-verify-then-authorize-C1-Attempt-002-execution
```

Repository integration hash: `sha256:9bffb8d2bc2516d1075c2a4615c4140b18b2eb2cc9068bac7581a1c7ed001e8f`.

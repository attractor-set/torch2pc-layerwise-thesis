# ADR-130: repository integration of the host-identity-corrected scientific image

[Русская версия](ADR-130-stage3b-qwake-c1-host-identity-corrected-scientific-image-freeze.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-c1-host-identity-corrected-scientific-image-freeze-v1/repository-integration.json -->

## Status

Accepted as the repository freeze of an already built and independently verified
scientific image. This record creates no new [attempt](../glossary_EN.md#term-attempt),
authorizes no C1 [execution](../glossary_EN.md#term-execution), and changes no
image or external [evidence](../glossary_EN.md#term-evidence) bytes.

## Context

ADR-129 corrected the container identity contract: the primary identity is bound
to the host `UID/GID`, ROCm `video`/`render` groups are supplementary, the output
directory is checked before `host-claim.json`, and `--cap-drop=ALL` remains in
force without adding `CAP_DAC_OVERRIDE`.

After PR #202 was merged and independently post-merge verified, a new scientific
image was built from exact tree `855889593a33bb6450e31cfc9feb152d14bd5292`. Its closed
[runtime](../glossary_EN.md#term-runtime) surface is the 157-path manifest
`sha256:fbfd01ecd41cc1615acef9f0fc9b3dd390e9605ebadd9a5dc86d78a425e2ac7b`.

Image and freeze identities:

```text
SOURCE_COMMIT=98cff5b2ecd64e1c96e19f0b04104ac00a5c3cf2
SOURCE_TREE=855889593a33bb6450e31cfc9feb152d14bd5292
HOST_IDENTITY_CORRECTION_SHA256=sha256:dd827f2ecb5fc983ad9d800961c34f61d443240651dc007526332fe6215d24aa
RUNTIME_SOURCE_MANIFEST_SHA256=sha256:fbfd01ecd41cc1615acef9f0fc9b3dd390e9605ebadd9a5dc86d78a425e2ac7b
IMAGE_DIGEST=sha256:12a4a6792530471517e53b30625bcfc45031a97bb9072f54bfa0c966e3fc2b5d
FREEZE_SHA256=sha256:ea207e6d31507d449e24fc30bb74fb21ec6560b1ec4a777cb1199de3ad63184f
ORIGINAL_EVIDENCE_SHA256SUMS_SHA256=sha256:051b3665616705f0538b7fdd78d43e15eae2fa05815d62848ec68fb4253004aa
REPOSITORY_INTEGRATION_SHA256=sha256:66369e9f6f666e94625f403c341028ae2249a7e74707c22b0fef75231b67fc46
```

## Decision

1. Copy the 18 original external-freeze files byte-for-byte without normalization.
2. Add only repository-integration authorization, the repeated independent
   verification log, the integration record, and `repository-SHA256SUMS`.
3. Treat image `sha256:12a4a6792530471517e53b30625bcfc45031a97bb9072f54bfa0c966e3fc2b5d` as the sole [candidate](../glossary_EN.md#term-candidate) for the next new C1
   request freeze after this integration is merged and separately post-merge
   verified.
4. Preserve image `sha256:89703b0b37b2729855835a6ed19ba1ca397ae14614c318344bd7625d12c727ef` and the previously frozen C1 request
   as historical artifacts. The old request is not reusable because it binds the
   predecessor source/image identities.
5. Do not open `Attempt-002`, C1/C2/C3/R, or publication through this ADR.

## Effect boundary

```text
ORIGINAL_EVIDENCE_BYTES_PRESERVED=true
SCIENTIFIC_IMAGE_MUTATED=false
DOCKER_BUILD_INVOKED=false
DOCKER_RUN_INVOKED=false
PREVIOUS_C1_REQUEST_REUSABLE=false
NEW_C1_REQUEST_FREEZE_REQUIRED=true
NEW_C1_REQUEST_FROZEN=false
NEW_C1_EXECUTION_AUTHORIZATION_ISSUED=false
ATTEMPT002_CREATED=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
PR_MERGED=false
```

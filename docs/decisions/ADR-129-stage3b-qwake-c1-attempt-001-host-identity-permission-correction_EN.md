# ADR-129: terminal `C1 Attempt-001` failure and scientific-host identity correction

[Русская версия](ADR-129-stage3b-qwake-c1-attempt-001-host-identity-permission-correction.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-c1-attempt-001-host-identity-permission-correction-v1/correction.json -->

## Status

Re-authored from post-merge verified `main` after the repository-wide
language-validation refactor; the semantics of the minimal source correction
after terminal consumption of `C1 Attempt-001` are unchanged. This
[attempt](../glossary_EN.md#term-attempt) must not be retried. This slice does
not build a new image, freeze a new C1 request, authorize `Attempt-002`, or
start a new [execution](../glossary_EN.md#term-execution).

## Cause

`C1 Attempt-001` consumed its scientific authorization through the exact
`host-claim.json`. The first embedded write effect,
`authorization-consumption.json`, then failed with `PermissionError`.

The read-only audit excluded rootless/userns. The host created the output
directory as the host UID/GID with mode `0775`; the image declared `root`, while
the launcher used `--cap-drop=ALL` and supplied no `--user`. Container UID 0
therefore lacked `CAP_DAC_OVERRIDE` and fell into Unix DAC class `other`, where
`0775` grants `r-x` but not write.

## Decision

1. Preserve `--cap-drop=ALL`, `no-new-privileges`, read-only rootfs, and
   `network=none`.
2. Do not restore `CAP_DAC_OVERRIDE`.
3. Bind container primary identity to host `uid:gid`.
4. Add host `video` and `render` GIDs as supplementary groups for ROCm.
5. Create the output directory as `0700`; before `host-claim.json`, verify owner
   UID plus owner write+execute.
6. An exact valid `host-claim.json` normatively means
   `AUTHORIZATION_CONSUMED=true` even without a terminal receipt; future
   execution wrappers must report it.
7. Preserve `C1 Attempt-001` and its
   [evidence](../glossary_EN.md#term-evidence) bytes unchanged.
8. Because the frozen [runtime](../glossary_EN.md#term-runtime) closure changes,
   a new scientific image and a new C1 request/authorization chain are required
   for `Attempt-002`.

```text
ATTEMPT001_AUTHORIZATION_CONSUMED=true
ATTEMPT001_RETRY_PERMITTED=false
ATTEMPT001_TERMINAL_FAILURE=true
CAP_DROP_ALL_PRESERVED=true
CAP_DAC_OVERRIDE_ADDED=false
CONTAINER_PRIMARY_IDENTITY_BOUND_TO_HOST_UID_GID=true
VIDEO_RENDER_SUPPLEMENTARY_GROUPS_BOUND=true
PRECLAIM_OUTPUT_OWNER_WRITE_CONTRACT=true
SUCCESSOR_RUNTIME_MANIFEST_SHA256=sha256:fbfd01ecd41cc1615acef9f0fc9b3dd390e9605ebadd9a5dc86d78a425e2ac7b
CORRECTION_SHA256=sha256:dd827f2ecb5fc983ad9d800961c34f61d443240651dc007526332fe6215d24aa
DOCKER_BUILD_INVOKED=false
DOCKER_RUN_INVOKED=false
ATTEMPT002_CREATED=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
```

# ADR-063: `QW-LC4-F` runtime freeze

[Russian version](ADR-063-stage3b-qwake-lc4-f-runtime-freeze.md)

- Status: accepted
- Date: July 27, 2026

## Context

[`QW-LC4-F` authoring](ADR-062-stage3b-qwake-lc4-f-runtime-freeze-authoring_EN.md)
froze the ordered source, request, image, preflight, static receipt, and
single-[attempt](../glossary_EN.md#term-attempt) authorization boundary.
Mechanism [execution](../glossary_EN.md#term-execution) remained closed.

Image
`sha256:a31cf96e20ab45ce29fe18b68eb805bd048a02f1f8107cf680d1c174ea363929`
was built from exact source commit
`51fc7537fdcb395145fc4c5a38b8918b018fe892`. CPU/ROCm
[runtime](../glossary_EN.md#term-runtime) checks and the canonical
authorization validator passed. No
[local compute](../glossary_EN.md#term-local-compute) occurred.

## Decision

1. Freeze the ten-file
   `stage3b-qwake-lc4-f-runtime-freeze-v1` package.
2. Bind it to the exact source, Torch2PC, image, request, `QW-LC4-I`
   implementation, `QW-LC3` contract, preflight, static receipt, and
   authorization identities.
3. Treat authorization as prospective and single-attempt: 14 runtime cells,
   168 matched cells, 28 reserve probes, and `execution_count=1`.
4. Do not treat authorization as execution. The package records
   `runtime_execution_permitted=true`,
   `runtime_execution_performed=false`, and no engineering
   [evidence](../glossary_EN.md#term-evidence).
5. Keep `QW-LC4-F` incomplete until merge and independent post-merge
   verification.
6. Only successful post-merge verification may permit the separate
   `QW-LC4-E` slice. Scientific execution, test
   [dataset](../glossary_EN.md#term-dataset) access, publication, and policy
   activation remain closed.

## Exact identities

```text
source_commit=51fc7537fdcb395145fc4c5a38b8918b018fe892
torch2pc_commit=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
image_digest=sha256:a31cf96e20ab45ce29fe18b68eb805bd048a02f1f8107cf680d1c174ea363929
preflight_sha256=sha256:3a8d7817338f3b93396270ea8e1b1b2fbda768dbd5461a18f97520948a53a9e6
authorization_sha256=sha256:d11b662a5c5eeada5333e69c6fddf2e50726c01b4d8c78a556a68167dbdd301e
manifest_file_sha256=sha256:4840d39d7c19133aeb3f20c572c17677f84ad2f82697dc4ad75dcccb99bb52c1
freeze_registry_sha256=sha256:8f8a0dfaaff934ac3c8f654e7e65d9460168755532547dcf924e51c6451aeb6d
source_registry_sha256=sha256:f80fe750b26afda55be19f9f2322baade6c7f07b11ee0d0a431ad88c1136d7b0
```

`manifest.json` has no self-digest. Its identity is the SHA-256 of the complete
file.

## Log provenance

The first static phase failed closed because of an invalid `MkDocs` option.
A clean retry passed all 22 checks.

The original raw build log was lost from temporary storage.
`image-build.log` is explicitly marked as a provenance reconstruction of the
already verified original image through `docker image inspect` and
`docker image history`. A separate rebuild is not identity evidence.

## Boundaries

```text
qwake_slice=QW-LC4-F
qwake_status=runtime_authorization_frozen_execution_not_performed
qwake_next_slice=QW-LC4-F-merge
qwake_post_merge_next_slice=QW-LC4-E
QW_LC4_F_MATERIALIZED=true
QW_LC4_F_COMPLETE=false
QW_LC4_E_BRANCH_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
```

## Consequences

Only a `QW-LC4-F` freeze PR may follow. The authorization must not be consumed
on this branch. After merge, an independent verification of the exact tree,
package, and closed boundaries is required.

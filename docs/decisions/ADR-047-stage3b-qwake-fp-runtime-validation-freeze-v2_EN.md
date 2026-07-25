# ADR-047: freeze of the new `QW-4B-F-v2` single-attempt runtime authorization

[Русская версия](ADR-047-stage3b-qwake-fp-runtime-validation-freeze-v2.md)

- **Status:** accepted as `QW-4B-F-v2`; one engineering [attempt](../glossary_EN.md#term-attempt) is permitted, but [execution](../glossary_EN.md#term-execution) and [evidence](../glossary_EN.md#term-evidence) are absent
- **Date:** 2026-07-24

```text
qwake_new_image_built=true
qwake_new_runtime_preflight_captured=true
qwake_new_runtime_authorization_issued=true
qwake_runtime_authorization_verified=true
qwake_runtime_validation_permitted=true
qwake_authorized_cell_count=6
qwake_authorized_execution_count=1
qwake_runtime_execution_performed=false
qwake_engineering_evidence_present=false
qwake_scientific_execution_open=false
qwake_next_slice=QW-4B-E-v2
```

## Context

ADR-046 retired the old `QW-4B-F-v1` [candidate](../glossary_EN.md#term-candidate) before execution and required a new immutable image after the documentation refactor. The new image was built from merge commit `e413bb1e13cee42f702512e499f994e90df21e45` and binds Torch2PC `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

Static, unit, and documentation checks passed again before authorization issuance. A live [runtime](../glossary_EN.md#term-runtime) preflight then bound CPU/float64 and ROCm/float32. No model cell was executed.

## Decision

### 1. Immutable identities

```text
source_commit=e413bb1e13cee42f702512e499f994e90df21e45
torch2pc_commit=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
image_digest=sha256:bd91fab26df5f91a3aba90b8cad38badccab3a1a7bfb20efe4126a88a13236c4
preflight_sha256=sha256:79ead4a0e757272c788acd90700d61c0e5a0509fe64168f83f47dc0963ce4d00
authorization_sha256=sha256:d22063efa0c458c2498577139fa322b952081d8356cd1a6511f25188b12206b6
receipt_chain_sha256=sha256:9eda60c6806581fea28021546b881d939e062c017b702a175105c56a25dea05d
authorized_output_root=results/stage-3/qwake-fp-runtime-validation-v2-attempt-001
```

The image, source, preflight, static-validation receipt, authorization, and verification log form one content-addressed chain.

### 2. Byte-preserved external inputs

Eight external files are copied without modification. `source-SHA256SUMS` preserves the source registry, while the new `SHA256SUMS` covers the complete frozen package, including its manifest. This is [integrity sealing](../glossary_EN.md#term-integrity-sealing), not model execution.

```text
source_registry_sha256=sha256:40ce845bc50dbbbdcc7aef5b4327e1325dd7bcda9c5c85a61ebb05024e045caa
package_registry_sha256=sha256:d6d9d6b4b4fb2614e928b16c8acd355508aebee7561254505828f9479ee31a30
source_files_preserved_byte_for_byte=true
```

### 3. Bounded authorization scope

```text
CPU/float64 × P0/P1/P2
ROCm/float32 × P0/P1/P2
model_seed=0
batch_id=synthetic-engineering-batch-v1
execution_count=1
```

The authorization opens only engineering runtime validation. The scientific campaign, test split, publication, scientific-image freeze, and `LOCAL_COMPUTE` remain closed.

### 4. Authorization verification is not execution

The official verifier rechecked source, Torch2PC, image, preflight, receipt chain, CPU/ROCm probes, and the absent output root. Verification did not call the execution command and did not consume the single attempt.

```text
authorization_verified=true
runtime_execution_performed=false
engineering_evidence_present=false
```

### 5. Next atomic slice

Only after `QW-4B-F-v2` is merged may a separate `QW-4B-E-v2` use this exact frozen package. It must create the output root exactly once and fail closed on any identity mismatch or pre-existing output.

`QW-LC0` remains closed until a successful sealed [baseline](../glossary_EN.md#term-baseline) engineering report.

## Consequences

`QW-4B-F-v2` establishes admission readiness. It does not establish observer non-interference or cost correctness under real execution. Those claims require `QW-4B-E-v2` and an independent result audit.

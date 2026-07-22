# Stage 3B descriptive-analysis output seal

[Русская версия](STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS-OUTPUT-SEAL.md)

## Purpose

This document specifies the technical freeze of the already executed 18-file [matched-profiling](../../docs/glossary_EN.md#term-matched-profiling) descriptive analysis. It does not rerun the analysis, change results, or act as a publication gate.

## Frozen roots

```text
output_root=results/stage-3/analysis/matched/stage3b-matched-descriptive-analysis-70d6c3c-v1
audit_root=experiments/frozen/stage3b-matched-descriptive-analysis-output-audit-v1
seal_root=experiments/frozen/stage3b-matched-descriptive-analysis-output-seal-v1
```

The output root contains exactly the 18 registered files. The audit root contains `audit.json`, `execution-receipt.json`, `OUTPUT-SHA256SUMS`, and `SHA256SUMS`. The seal root contains `seal.json` and `SHA256SUMS`.

## Identities

```text
execution_source_commit=72b95a284e8747a33b8c34d5929d4110aa4bfea1
request_digest=5c813e101c17210443b63b6499c7c6fed88fe34029f438942b71ad9faf127a2e
authorization_digest=5e4f570d81d373637244563afed9d1765fe0d17b3d726db9282b4104c37d83c0
runtime_preflight_digest=428c9a7fdc1baf2b86a033a12189b9b98cce4e41dbb6e87cb73d42f4e9e901cc
runtime_identity_digest=e71f0f8539231e466291843e919b412d44ec6022e4dce863785142b67abe007d
execution_receipt_sha256=997569220aa89261e0d375a70597bb8325186f1739a7977e3a211fce1ffcf8b2
output_registry_sha256=8baa1b55c21ed2b00bd849bbbe4f415d8b5f86d70bd9989d4ec4917765ead1da
audit_record_sha256=a2bfbfc8f57cc681b535e8a8ab0e722fd745f49df9eab8094a6e70e8adb88123
audit_package_registry_sha256=c7984a0559c8ee2c902583abd547dec84f23116b679cdf6cfae665ca167d00c6
seal_digest=dbb8983bd77490ca4feedc035ae31ca4cdd0764ecd89dab1b0c3d91aed0ad3cd
```

## Output immutability

Sealing adds no file inside the output root and does not rewrite generated metadata. The generated output retains `analysis_output_evidence=false` as the historically exact immediate post-execution boundary. The external `seal.json` separately establishes `analysis_output_sealed=true` and `analysis_output_evidence=true` for the unchanged file set.

## Claim boundary

```text
analysis_execution_performed=true
analysis_results_present=true
analysis_output_audited=true
analysis_output_sealed=true
analysis_output_evidence=true
results_publication_permitted=false
release_publication_permitted=false
superiority_claim_permitted=false
test_dataset_access=false
ex_if0_opened=false
policy_activation_permitted=false
```

Until a separate publication gate, result publication, superiority claims, `EX-IF0`, test-split access, and policy activation remain prohibited.

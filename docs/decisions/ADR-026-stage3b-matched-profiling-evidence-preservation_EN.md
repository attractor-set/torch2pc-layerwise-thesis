# ADR-026: matched-profiling evidence preservation and draft release

[Русская версия](ADR-026-stage3b-matched-profiling-evidence-preservation.md)

- **Status:** accepted
- **Date:** 21 July 2026

## Context

The new `v2` [matched-profiling](../glossary_EN.md#term-matched-profiling)
package was prospectively bound to the sealed `EQ-B1` and `EQ-B2` admissions.
After the immutable image, separate ROCm/float32 preflight, authorization,
non-measuring plan, and fail-closed boundary checks, exactly 288 cells were
executed in 96 matched blocks. Every [attempt](../glossary_EN.md#term-attempt) completed successfully, no retry
was required, and [runtime](../glossary_EN.md#term-runtime) validation confirmed a complete and consistent
[execution](../glossary_EN.md#term-execution) contour.

A separate [integrity seal](../glossary_EN.md#term-integrity-sealing) produced a
compact [evidence](../glossary_EN.md#term-evidence) package. Sealing set
`evidence=true` while retaining `results_publication_permitted=false` and
`full_stage3b_campaign_complete=false`. Evidence preservation therefore does
not authorize descriptive analysis, result publication, or the next
experimental stage.

## Decision

Preserve the sealed set byte-for-byte at:

```text
results/stage-3/profiling/matched/
  stage3b-matched-profiling-e1dcfb2-v1/
```

The repository preserves a lossless compressed representation in exactly 13 files:

```text
SHA256SUMS
SEALED-SHA256SUMS
analysis_metadata.json
attempt-history.jsonl
block-correctness.jsonl
environment-lock.json
locality_events.asset.json
locality_events.jsonl.zst
profiling_cells.csv
profiling_repetitions.csv
profiling_summary.csv
runtime-inventory.json
seal.json
```

`SEALED-SHA256SUMS` is the byte-identical registry created by sealing. The
6.09 GiB `locality_events.jsonl` stream is stored losslessly as a 23.9 MiB
Zstandard archive. `locality_events.asset.json` binds the compressed SHA-256,
the original SHA-256 and size, the compression parameters, and the draft
release asset name. All other sealed files remain byte-identical.

`seal.json` must record:

```text
scope=stage3b_b1_b2_matched_sealed_evidence_v1
status=sealed
source_commit=e1dcfb26823e1191b98d2aa2a598499b13197583
image_digest=sha256:3c269b4278026b5b69968b3265b506ce626f2baf693859989de3371d639da4d0
matched_cell_count=288
attempt_history_count=288
cross_candidate_correctness_block_count=96
retried_cell_count=0
evidence=true
full_lane_complete=true
full_stage3b_campaign_complete=false
results_publication_permitted=false
test_dataset_access=false
```

[Candidate](../glossary_EN.md#term-candidate) coverage must remain symmetric: 96 cells each for
`stage2_baseline`, `isolated_layer_vjp`, and `composite_vjp`. The repetition
table contains 1,440 rows, the summary table contains 96 rows, and the locality
event stream covers all 288 cells.

## Boundary after preservation

After this PR, the machine-checkable boundary is:

```text
matched_profiling_execution_open=false
matched_profiling_execution_complete=true
matched_profiling_runtime_validation=valid
matched_profiling_evidence=sealed
matched_profiling_analysis_open=false
runtime_authorization=issued_consumed
measurements_allowed=false
results_publication_permitted=false
release_draft_required=true
release_publication_permitted=false
full_stage3b_campaign_complete=false
test_dataset_access=false
```

The authorization is consumed and does not permit new
[execution](../glossary_EN.md#term-execution). Any new measurement campaign
requires a new empty output root and separate authorization.

## Release contour

After the evidence PR is merged and CI succeeds, create the immutable tag:

```text
stage3b-matched-profiling-evidence-v1
```

A dedicated workflow creates a **draft-only** GitHub Release. Its repository
assets include the sealed evidence archive, `RELEASE-MANIFEST.json`,
`RELEASE-NOTES.md`, and `SHA256SUMS`.

The local packager may additionally prepare:

```text
stage3b-matched-profiling-control-plane-v1.tar.gz
stage3b-matched-profiling-runtime-records-v1.tar.gz
stage3b-matched-profiling-image-checkpoint-v1.tar.gz
stage3b-matched-profiling-sealing-logs-v1.tar.gz
stage3b-matched-profiling-release-source-record-v1.json
```

These assets are built only from the previously verified external
`release-source-record.json`. The packager rechecks the control plane,
non-measuring plan, full execution journal, image [checkpoint](../glossary_EN.md#term-checkpoint), and sealing logs.
It neither mutates evidence nor publishes the release.

While `release_publication_permitted=false`, the workflow and local packager
must keep the release in draft state. Publication requires a separate decision
after descriptive analysis and publication-boundary review.

## Consequences

### Positive

- the full computational run becomes a verifiable repository artifact without storing a 6.09 GiB Git blob;
- all 288 cells and 96 blocks are bound to the exact image, source commit, and
  immutable file registry;
- run artifacts can be attached to a draft GitHub Release without committing
  the large raw runtime tree to Git;
- descriptive analysis can consume only the published sealed root.

### Limitations

- evidence preservation is not a comparative-analysis result;
- claims that B1 or B2 is superior remain prohibited;
- `EX-IF0`, `ECZ`/`NCZ` policies, `A11-OFF0`, `A11-OFF1`, and `QWake-PC`
  remain closed;
- the test split remains closed;
- public release publication is prohibited until a separate publication gate.

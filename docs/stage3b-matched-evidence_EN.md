# Stage 3B matched evidence pipeline

This document describes the post-ADR-015 artifact boundary.

## Runtime cell artifacts

Every successful cell [attempt](glossary_EN.md#term-attempt) contains:

- `request.json`;
- `started.json`;
- `resolved-config.json`;
- `environment.json`;
- `measurements.json`;
- `locality-events.jsonl`;
- `completed.json`.

`measurements.json` separates:

- `primary_timing_measurements` (`no_hooks`);
- `structural_timing_measurements` (`counters_only`);
- `observer_cost_measurements`;
- `region_measurements`;
- `structural_measurements`;
- `integrity_measurements`.

The primary timing lane is never corrected by subtracting [observer cost](glossary_EN.md#term-observer-cost).

## Sealing

Validate without producing [evidence](glossary_EN.md#term-evidence):

```bash
python scripts/seal_stage3b_matched.py \
  --validate-only \
  --runtime-root "$OUTPUT_ROOT" \
  --matched-manifest \
    experiments/frozen/stage3b-matched-profiling-v2/manifest.json \
  --expected-source-commit "$PROJECT_SOURCE_COMMIT" \
  --expected-image-digest "$IMAGE_DIGEST" \
  --expected-authorization-token "$AUTHORIZATION_TOKEN"
```

Seal only from a clean sealing commit and into a new empty output directory.
The seal creates:

- `profiling_cells.csv`;
- `profiling_repetitions.csv`;
- `locality_events.jsonl`;
- `profiling_summary.csv`;
- `analysis_metadata.json`;
- `environment-lock.json`;
- `runtime-inventory.json`;
- `seal.json`;
- `SHA256SUMS`.

Sealing sets `evidence=true` but keeps
`results_publication_permitted=false`.

The completed evidence package is preserved at:

```text
results/stage-3/profiling/matched/
  stage3b-matched-profiling-e1dcfb2-v1/
```

It contains 288 cells, 1,440 repetition rows, 96 matched-block summaries,
288 append-only [attempt](glossary_EN.md#term-attempt) histories, 96 untimed
cross-[candidate](glossary_EN.md#term-candidate) correctness records, locality
events for every cell, the environment lock, and the
[runtime](glossary_EN.md#term-runtime) inventory. Preservation does not open descriptive analysis.

After the evidence PR and green CI, tag
`stage3b-matched-profiling-evidence-v1` creates a draft-only GitHub Release.
Repository evidence is packaged by
`scripts/package_stage3b_matched_release.py --mode repository`; the local
`--mode full` additionally packages the control plane, run records, image
[checkpoint](glossary_EN.md#term-checkpoint), and sealing logs from the verified external release-source record.
Public release publication remains prohibited.

## Analysis

```bash
python scripts/analyze_stage3b_matched.py \
  --evidence-root <sealed-root> \
  --output-root <new-analysis-root>
```

The analysis pairs candidates with `stage2_baseline` inside the same matched
block. It aggregates measured steps to repetitions, repetitions to cells, and
then reports descriptive summaries across model seeds. No p-values or
superiority claim are generated at `n=3`.

An engineering continuation eligibility flag does not open EX-IF0 and does not
permit policy activation.

## Repair gate before a new 288-cell campaign

After `ADR-017`, production
[execution](glossary_EN.md#term-execution) is fail-closed. A new freeze and
authorization do not replace the scientific gate. Launch simultaneously
requires:

- confirmatory `EQ-B1` with `120/120` matched pairs;
- confirmatory `EQ-B2` with `120/120` triples and `240/240` comparisons;
- exact [candidate](glossary_EN.md#term-candidate)-order balance per method: all
  six permutations eight times, `16/16/16` positions, and `24/24` pairwise
  precedence;
- one untimed cross-candidate correctness record per
  [profiling](glossary_EN.md#term-profiling) block;
- a new empty output root, new immutable image, and new authorization.

Retry is permitted only for records with `retry_eligible=true` and failure class
`infrastructure`, `operator_interruption`, or `system_interruption`. Scientific,
correctness, and unknown failures block retry and sealing. Sealing preserves
`attempt-history.jsonl` and `block-correctness.jsonl`; there must be exactly one
successful attempt and it must be last.

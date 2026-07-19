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
    experiments/planned/STAGE3B-B1-B2-MATCHED-PROFILING-MANIFEST.json \
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

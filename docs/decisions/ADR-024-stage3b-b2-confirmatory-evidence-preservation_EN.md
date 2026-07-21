# ADR-024: preservation of Stage 3B B2 confirmatory evidence

[Русская версия](ADR-024-stage3b-b2-confirmatory-evidence-preservation.md)

- **Status:** accepted
- **Date:** 20 July 2026

## Context

The confirmatory B2 contract was preregistered as 120 matched triples and 240
direct comparisons for `FixedPred` and `Strict` across CPU `float64` and ROCm
`float32` lanes. After request freezing, fail-closed environment checks, a
separate engineering smoke, and a non-measuring full-matrix plan, all 120
triples were executed. The [attempt](../glossary_EN.md#term-attempt) lifecycle completed without failed triples,
and `EQ-B2-CONFIRMATORY` was positively sealed.

The derived `EQ-B2` decision is linked to the confirmatory decision by its
SHA-256 and is not derived from the engineering smoke. The test [dataset](../glossary_EN.md#term-dataset) was not
accessed.

## Decision

Preserve the byte-for-byte sealed [evidence](../glossary_EN.md#term-evidence) set at:

```text
results/stage-3/b2/stage3b-b2-confirmatory-63885e5-v1/
```

The set contains exactly these 11 files:

```text
SHA256SUMS
attempt-history.jsonl
authorization.json
decision.json
direct-b1-b2-metrics.csv
endpoint-metrics.csv
matched-profiling-admission.json
request.json
resolved-config.json
structural-events.jsonl
trajectory-metrics.csv
```

`decision.json` must record:

```text
decision_id=EQ-B2-CONFIRMATORY
scope=confirmatory
status=pass
sealed=true
matched_triples_expected=120
matched_triples_observed=120
pairwise_comparisons_expected=240
pairwise_comparisons_observed=240
failed_pair_count=0
failed_pairs=[]
failed_triples=[]
dangerous_misses=0
test_dataset_access=false
results_publication_permitted=false
```

All five registered gates — `STRUCT-B2`, `NUM-B2`, `TRAJ-B2`, `OBS-B2`, and
`PROV-B2` — must have `passed=true` and an empty failed-triple list.

`matched-profiling-admission.json` must record the derived `EQ-B2` decision,
reference `EQ-B2-CONFIRMATORY`, contain the SHA-256 of `decision.json`, and
repeat the positive indicators without retrospectively changing the source
decision.

## Admission boundary

Positive confirmatory B2 completes the B1/B2 scientific-admission chain, but it
does not authorize use of the previous matched-[profiling](../glossary_EN.md#term-profiling) request. That request
was created before confirmatory B2 and remains only as a historical artifact.

The next admissible transition is:

```text
sealed EQ-B1 + sealed EQ-B2
→ new versioned matched-profiling request/manifest freeze
→ separate image/preflight/authorization/dry-run gates
→ only then 288-cell execution
```

After this PR the boundary remains closed:

```text
scientific_admission=open_after_eq_b2_confirmatory
matched_profiling_request_refresh_required=true
matched_profiling_execution_open=false
runtime_authorization=not_issued
measurements_allowed=false
test_dataset_access=false
```

Neither evidence preservation nor the derived `EQ-B2` authorizes matched
profiling, `EX-IF0`, `A11-OFF0`, `A11-OFF1`, the predictor, `QWake-PC`, or test
split access.

## Integrity and reproducibility

- `SHA256SUMS` verifies every sealed payload file;
- `attempt-history.jsonl` contains exactly 120 completed records and 120 unique
  `triple_id` values;
- the aggregate files cover 120 triples and 240 direct comparisons;
- `structural-events.jsonl` contains 1,800 events: 600 for `FixedPred` and
  1,200 for `Strict`;
- authorization before sealing retains `evidence=false`; scientific evidence
  is created only by the positively sealed decision and its linked set;
- previously published B1, B2-smoke, and matched-profiling artifacts are not
  rewritten.

## Consequences

### Positive

- B2 confirmatory equivalence becomes a repository-verifiable artifact;
- the B1/B2 admission chain is complete without test-split access;
- a new matched-profiling freeze may now be prepared prospectively.

### Limitations

- the full Stage 3B program remains incomplete;
- B2 performance has not yet been measured in the refreshed 288-cell campaign;
- the previous matched-profiling request/manifest is not admitted
  retrospectively;
- the evidence is not a universal claim outside the registered models, seeds,
  batches, methods, dtypes, and environment.

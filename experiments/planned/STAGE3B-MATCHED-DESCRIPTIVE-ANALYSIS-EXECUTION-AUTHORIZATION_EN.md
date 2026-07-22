# Stage 3B matched descriptive-analysis execution-authorization freeze

[Русская версия](STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS-EXECUTION-AUTHORIZATION.md)

## Purpose

This slice freezes a separate prospective authorization for exactly one future
read-only descriptive-analysis attempt. It does not invoke the executor, create
an attempt receipt, read metric values, or create results.

## Canonical package

Path:
`experiments/frozen/stage3b-matched-descriptive-analysis-execution-authorization-v1/`.
The package contains only:

- `authorization.json`;
- an exact copy of the frozen `runtime-preflight.json`;
- `SHA256SUMS`.

Validation rejects extra files, directories, symlinks, duplicate checksum
records, and any request/preflight/runtime binding mismatch.

## Authorized scope

Authorization freezes `execution_count=1`, the exact operator acknowledgement,
and one output root. It permits analysis execution while simultaneously
recording that execution has not occurred, results are absent, the test split
remains closed, and publication is not permitted.

## Operational boundary

The package alone does not open execution on a branch or pull request. The
executor is admissible only after merge into a clean `main`, renewed runtime
identity verification, an absent output root, and an absent local receipt for
the request digest. Once claimed, replay remains forbidden even if the output
root is deleted.

```text
execution_authorization_present=true
analysis_execution_permitted=true
analysis_execution_performed=false
execution_attempt_claimed=false
analysis_results_present=false
results_publication_permitted=false
release_publication_permitted=false
```

# Stage 3B matched descriptive-analysis execution request

[Русская версия](STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS-EXECUTION-REQUEST.md)

## Status

```text
request_id=stage3b-matched-descriptive-analysis-execution-request-v1
request_frozen=true
execution_authorization_present=false
analysis_execution_permitted=false
analysis_execution_performed=false
analysis_results_present=false
results_publication_permitted=false
release_publication_permitted=false
```

This document is a **request**, not an admission. It grants no right to read
sealed numeric values through the analyzer, create the output package, or
publish results.

## Frozen identities

The request binds:

- hardening-base commit
  `70d6c3ca971415f57805dbf9b2ed4bbb80b2d873`;
- evidence tag `stage3b-matched-profiling-evidence-v1` and commit
  `21ddfb8840674871f0b9d888b36397f5cf0e111b`;
- profiling source commit
  `e1dcfb26823e1191b98d2aa2a598499b13197583`;
- frozen protocol SHA-256
  `074510f1212f1eceb41da8b42ab52f1fd9d816c3901f2a3b8e4e7afec59a3209`;
- analysis-core SHA-256
  `0e9f55fc337b7870923a087308f370afc54bdce97501ce462c1033062a322462`;
- all nine SHA-256 identities of the sealed input package, including the
  compressed locality stream.

The machine-readable source is:

`experiments/frozen/stage3b-matched-descriptive-analysis-execution-request-v1/request.json`.

## Requested execution

At most one read-only run is requested after a separate admission. That
admission must:

1. bind the exact `request_digest`;
2. freeze runtime identity and exact `generated_at_utc`;
3. verify unchanged protocol and analysis core;
4. verify all input SHA-256 identities before and after execution;
5. confirm that the output directory is absent;
6. prohibit a second run;
7. keep publication closed after result creation.

## Output contract

The only requested directory is:

`results/stage-3/analysis/matched/stage3b-matched-descriptive-analysis-70d6c3c-v1`.

It must not exist before authorized execution. Successful execution must
atomically create exactly the 18 top-level files already listed in the frozen
protocol and `request.json`. A partial or additional inventory fails closed.

## Next gate

A separate PR may next contain runtime preflight and machine-readable
authorization only. Until it merges, the following remain prohibited:

- invoking the sealed-evidence engine;
- creating the output directory;
- computing comparative metrics;
- selecting a candidate;
- publishing the draft release;
- opening `EX-IF0`.

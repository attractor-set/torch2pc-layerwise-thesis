# ADR-031: implement the Stage 3B matched descriptive-analysis runtime preflight

[Русская версия](ADR-031-stage3b-matched-descriptive-analysis-runtime-preflight-implementation.md)

- **Status:** accepted
- **Date:** 2026-07-21

## Context

ADR-030 froze the request for one future [run](../glossary_EN.md#term-run), but
it did not freeze the [runtime](../glossary_EN.md#term-runtime) or issue
`authorization`. A verifiable admission layer must bind repository state,
the Python and `Zstandard` executables, NumPy and Matplotlib versions and
modules, immutable inputs, and an absent output directory without reading
observed metric values.

## Decision

Add a separate runtime-preflight module and two narrow CLIs:

- `preflight_stage3b_matched_analysis.py` writes only a [candidate](../glossary_EN.md#term-candidate)
  `runtime-preflight.json`;
- `execute_stage3b_matched_analysis.py` accepts neither an external
  authorization path nor a generation timestamp and uses only the future
  frozen package at its canonical repository path;
- the verifier requires exact binding of `request_digest`, `preflight_digest`,
  `runtime_identity_digest`, `generated_at_utc`, the single output root, and
  operator acknowledgement;
- the verifier accepts only the exact three-file package of regular files and
  rejects symlinks, directories, additional entries, and duplicate
  `SHA256SUMS` records;
- before computation, the executor atomically claims one
  [attempt](../glossary_EN.md#term-attempt) for the `request_digest` in Git
  administrative storage, runs the engine only in a
  staging directory, rechecks all input SHA-256 identities, and only then
  atomically publishes the canonical output root.

The preflight computes only SHA-256 identities, validates clean Git state,
executable and direct numerical-dependency identities, output-root absence, and
the `Zstandard` frame. It does not parse CSV or JSONL metric values.

## Decision boundary

```text
runtime_preflight_implemented=true
runtime_preflight_artifact_frozen=false
execution_authorization_present=false
analysis_execution_permitted=false
analysis_execution_performed=false
analysis_results_present=false
results_publication_permitted=false
release_publication_permitted=false
```

No authorization package enters this PR, and the public executor remains closed
until a separate merge.

## Consequences

Benefits:

- runtime identity can be frozen after merge without a circular dependency on
  the not-yet-known merge commit;
- the CLI cannot accept an external or substituted authorization;
- a repeated attempt for the same `request_digest` fails closed through an
  atomically created local receipt even if the output root is removed;
- the canonical output root appears only after the input SHA-256 check following
  [execution](../glossary_EN.md#term-execution);
- `generated_at_utc` comes only from frozen authorization and cannot predate
  the runtime preflight.

Limitations:

- the actual runtime preflight is not frozen yet;
- authorization is not issued;
- sealed [evidence](../glossary_EN.md#term-evidence) is not analyzed;
- the single-attempt receipt is local to the canonical Git clone; the future
  authorization procedure must explicitly identify that execution workspace;
- the draft release remains unpublished.

# Stage 3B matched descriptive-analysis runtime-preflight implementation

[Русская версия](STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS-RUNTIME-PREFLIGHT.md)

## Purpose

This slice implements fail-closed runtime admission for the already frozen
execution request. It does not create authorization, execute analysis, or read
observed metric values.

## Verified identity

The runtime preflight binds:

- the exact Git commit and clean worktree;
- versions, paths, and SHA-256 identities of the Python and `Zstandard`
  executables;
- NumPy and Matplotlib versions, module paths, and module SHA-256 identities;
- SHA-256 identities of the analysis core, runtime module, and both CLIs;
- the frozen protocol and execution request;
- nine sealed-evidence SHA-256 identities;
- structural validation of `locality_events.jsonl.zst`;
- absence of the single requested output root.

## Future authorization contract

The verifier requires a separate frozen package containing:

1. `runtime-preflight.json`;
2. `authorization.json`;
3. `SHA256SUMS`.

Authorization must bind the request, preflight, and runtime digests, freeze
`generated_at_utc` no earlier than the runtime preflight, permit exactly one
read-only attempt, and keep publication closed. The exact package admits only
three regular files without symlinks, directories, or duplicate `SHA256SUMS`
records.

## Executor boundary

The executor accepts neither an external authorization path nor
`generated_at_utc`. Until the canonical frozen package exists, it exits before
calling the computational engine. After admission it atomically claims a local
attempt receipt for the `request_digest`, computes only in a staging directory,
and publishes the output root only after the post-execution input SHA-256 check.

```text
runtime_preflight_implemented=true
runtime_preflight_frozen=true
execution_authorization_present=false
sealed_evidence_execution=false
analysis_results_present=false
results_publication_permitted=false
```
## Frozen artifact

The actual preflight captured without reading observed metric values is frozen
at `experiments/frozen/stage3b-matched-descriptive-analysis-runtime-preflight-v1/`.
It binds merge commit `272a9258f70320416ff97c3da076435fd5334bc4`,
request digest `5c813e10…127a2e`, runtime identity `e71f0f85…007d`, and
preflight digest `428c9a7f…901cc`. The file SHA-256 of
`runtime-preflight.json` is
`1722cce133e047512c2b587c9d8fba15e95457653afd2fa496f295d3b1bbced0`.

The freeze does not create authorization, claim an execution attempt, or open
analysis or publication.

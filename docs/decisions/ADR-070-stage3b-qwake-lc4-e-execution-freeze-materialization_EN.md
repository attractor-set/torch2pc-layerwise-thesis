# ADR-070: QW-LC4-E execution-freeze materialization

- Status: accepted
- Date: 2026-07-28
- Slice: `QW-LC4-E-execution-freeze-materialization`

## Context

PR #130 materialized the concrete bounded
[runtime](../glossary_EN.md#term-runtime) backend and the one-shot entrypoint.
Independent post-merge verification bound `main` to `67a084c0b970ad79ad0692442f660085a73b080a`. A separate
immutable image and canonical `execution-freeze-v1` package are required before
an explicit one-shot engineering
[execution](../glossary_EN.md#term-execution) can be considered.

## Decision

1. Image `torch2pc-layerwise-thesis:0.1.0-qw-lc4-e-freeze-67a084c0b970` is built from exact commit `67a084c0b970ad79ad0692442f660085a73b080a` on pinned base
   image `rocm/pytorch@sha256:96a2fb24dec9896e2f8238178f0c49d0dcc4c7dcc597be09e4564316bd86d191`.
2. Its local image ID and content address are `sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d` and its size is
   `10900539047` bytes.
3. The nine-file `experiments/frozen/stage3b-qwake-lc4-e-execution-freeze-v1` package preserves canonical
   `execution.json`, a materialization manifest, and the complete image-input
   receipt chain.
4. `execution.json` contains `runtime_execution_permitted=true` because it
   describes the future one-shot entrypoint capability after environment
   verification. It does not open the branch-level gate, which remains
   `branch_runtime_execution_permitted=false`.
5. The lease, output root, and runtime staging directory remain absent.
6. A separate explicit one-shot engineering invocation authorization is still
   required after merge; this materialization does not execute anything.

## Consequences

- the immutable image and execution-freeze package become independently
  verifiable;
- exact backend and entrypoint SHA-256 identities are bound to the image;
- retry after lease claim remains prohibited;
- engineering [evidence](../glossary_EN.md#term-evidence), scientific
  execution, [test-dataset access](../glossary_EN.md#term-test-dataset-access)
  to the test [dataset](../glossary_EN.md#term-dataset), and publication remain
  closed.

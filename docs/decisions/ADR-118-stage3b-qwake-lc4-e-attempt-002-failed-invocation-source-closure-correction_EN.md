# ADR-118: terminal attempt-002 and temporal source-closure correction

- **Status:** accepted as a non-executing corrective authoring decision
- **Date:** 2026-08-05
- **Related decisions:** ADR-113, ADR-114, ADR-115, ADR-117

## Context

The one-shot ADR-117 invocation reached the operation entrypoint, delegated
transition, and `docker run`, but the container failed before lease-v1
materialization. A durable host outcome exists; lease and output root are
absent; authorization was not consumed under lease semantics.

The image was built from commit
`02afcc3e79b2d456cc3f1c075d4d792a0be608f7`. Against the final
[execution](../glossary_EN.md#term-execution)-freeze `source-SHA256SUMS`, that commit contains ten byte-exact
paths and lacks two paths:

- `scripts/verify_stage3b_qwake_lc4_attempt_002_execution_freeze.py`;
- `tests/unit/test_stage3b_qwake_lc4_attempt_002_execution_freeze.py`.

Execution-freeze materialization commit
`2f346498a28377d355b88560aa099890f829af46` already contains both paths,
but their contents do not yet match the final registry: ten paths are
exact and two have hash mismatches.

The first commit where all twelve registry entries simultaneously exist
and match byte-for-byte is authorization commit
`b5b29be5802641287e6e29bb42240ad9e41744b4`.

Therefore, image source, execution-freeze materialization, and final
registry identity belong to three different temporal snapshots. Host
preflight checked the current control-plane tree, while [runtime](../glossary_EN.md#term-runtime) checked
the older image `/workspace`.

## Decision

1. [Attempt](../glossary_EN.md#term-attempt)-002 is terminal as a failed irreversible attempt.
2. The durable outcome, freeze-v1, authorization-v1, host chain, operation,
   and both invocation scripts remain immutable.
3. Attempt-002 retry and reuse of its authorization decision are forbidden.
4. The next compute invocation uses attempt-003 identity and disjoint
   effect paths.
5. Runtime source registry and host authoring source registry are separated.
6. Every runtime registry path is verified against the exact source-commit
   blob before build.
7. After `COPY . /workspace`, Docker build verifies the runtime registry.
8. A post-build gate verifies image digest, OCI revision, and container-side
   source closure without model or [dataset](../glossary_EN.md#term-dataset) execution.
9. Future authorization is issued only after complete image/source-closure
   proof.

## Boundary

This slice does not build an image, start a container, create attempt-003,
issue authorization, create lease/output, permit PR #179 merge, or open
QW-5.

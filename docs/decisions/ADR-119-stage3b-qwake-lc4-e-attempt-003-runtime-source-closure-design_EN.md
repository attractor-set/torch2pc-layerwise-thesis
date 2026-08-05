# ADR-119: source-closure design for `attempt-003`

## Status

Accepted as bounded design authoring without computational effects.

## Context

`attempt-002` ended as an irreversibly failed
[attempt](../glossary_EN.md#term-attempt). The next identity,
`stage3b-qwake-lc4-runtime-validation-v1-attempt-003`, is not a retry of the previous attempt.

The failure showed that a host-side registry is insufficient to prove that
every required file is present in a future image. The new contract separates
design from [execution](../glossary_EN.md#term-execution) and requires source
closure before any image build, `authorization`, or external effect.

## Decision

1. Freeze a machine-readable `contract.json` with the new `attempt_id`,
   `results/stage-3/qwake-lc4-runtime-validation-v1-attempt-003`, and new identities for every future package.
2. The future [runtime](../glossary_EN.md#term-runtime) package must contain
   `runtime-SHA256SUMS` covering every build and runtime input listed by the
   contract.
3. Before `docker build`, each path is verified as a Git object, its blob
   bytes are checked by SHA-256, and inclusion is checked against
   `.dockerignore`. The result is stored as a deterministic closure report.
4. After `COPY . /workspace`, the Dockerfile must run `sha256sum -c` against
   `runtime-SHA256SUMS` before final image identity is fixed.
5. After build, the OCI revision must equal the exact source commit; the
   image digest must be new; build-time proof and non-executing
   container-side verification are mandatory.
6. Reuse of the `attempt-002` `authorization`, image identity, lease, or
   outcome is forbidden.
7. In this slice, [run](../glossary_EN.md#term-run), model invocation,
   [dataset](../glossary_EN.md#term-dataset) access, lease/outcome creation,
   Docker build/run, freeze or host-chain materialization, `PR #179` merge,
   remote `main` modification, and `QW-5` opening are forbidden.

## Boundary

This ADR defines design authoring only. It does not implement runtime,
materialize `runtime-SHA256SUMS`, create an image, freeze, host chain,
`authorization`, operation, lease, output root, or durable outcome.

A separate explicit authorization is required for implementation authoring,
image build, freeze materialization, host-chain authoring, authorization
issuance, operation authoring, and actual execution.

# ADR-114: attempt-003 execution-freeze materialization implementation

## Status

Accepted as a bounded implementation of the future materialization mechanism.

## Context

ADR-113 bound [attempt](../glossary_EN.md#term-attempt)-003 to the exact merged
source commit `541b34a57297d2c5a82851bd846b583d4904fba6`, the 13-path source closure,
the pinned base image, and the requirements for a future
[execution](../glossary_EN.md#term-execution) freeze. No new image has been
built, no image identity has been materialized, and the execution freeze is
still absent.

The existing `Attempt003ExecutionFreeze` already defines the canonical
`execution.json` schema. This slice therefore does not introduce another
freeze contract and does not create
`stage3b-qwake-attempt-003-execution-freeze-v1`.

## Decision

Add a pure file materializer that may be invoked only after a separately
authorized image build and non-executing image inspection. It accepts exactly
five immutable receipts: `identity.env`, `image-build.log`,
`image-capture.json`, `image-inspection.json`, and
`static-image-validation.json`.

The verified fields in `image-inspection.json` are authoritative for image
identity. The other receipts are retained as input
[evidence](../glossary_EN.md#term-evidence) without inventing additional
semantics.

Before writing, the materializer verifies the exact source commit and OCI
revision, pinned OCI base image, image/repository digest consistency, exact
SHA-256 identities of the four [runtime](../glossary_EN.md#term-runtime)
components, exact Torch2PC commit, scientific authorization, and the closed
effect boundary.

It then constructs the existing `Attempt003ExecutionFreeze`, computes its
canonical digest, and creates the nine-file package in a sibling staging
directory. The destination must not exist, replacement is forbidden, and the
validated staging directory is atomically renamed to the canonical path.

## Boundary

This slice implements only the future materialization capability. It does not
build or run Docker, materialize an image identity now, create the execution
freeze now, issue or consume an attempt-003 authorization, create a lease or
outcome, invoke runtime or model code, or access a
[dataset](../glossary_EN.md#term-dataset).

The future materializer requires a separate operation after real build and
inspection receipts exist.

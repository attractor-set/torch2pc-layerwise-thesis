# ADR-071: QW-LC4-E one-shot engineering invocation authorization

- Status: accepted
- Date: 2026-07-28
- Slice: `QW-LC4-E-one-shot-engineering-invocation-authorization`

## Context

PR #131 was merged into `main` as `375db196b615f7024cd5f715de9c9be7b526a9f7` and independently
verified. The immutable image, `execution-freeze-v1`, one-[attempt](../glossary_EN.md#term-attempt) admission,
168-cell matrix authorization, and one-shot entrypoint already exist.
Materializing those capabilities is not the same as authorizing one concrete
invocation.

## Decision

1. Materialize the four-file `experiments/frozen/stage3b-qwake-lc4-e-one-shot-engineering-invocation-authorization-v1` package.
2. `authorization.json` authorizes exactly one future engineering invocation,
   one future lease claim, and future [execution](../glossary_EN.md#term-execution)
   of the synthetic matrix.
3. The record binds the merge commit, Torch2PC, immutable image, execution
   freeze, admission, matrix authorization, backend, wrapper, and entrypoint
   by exact SHA-256 identities.
4. Internal future permission does not open the branch-level effect:
   `branch_runtime_execution_permitted=false`.
5. This slice does not create the lease, result root, or staging tree, consume
   authorization, or invoke model code.
6. A separate host-side invocation wrapper must verify this package before it
   can invoke the exact immutable image.

## Identities

- issued at: `2026-07-28T22:54:56Z`;
- semantic SHA-256: `sha256:0a60dacc1bfd5073cf52d76f2ec33ae54f00899aad9877d44607199659fda75a`;
- package registry: `sha256:9a47f79e9607db98a2c7c224c25cbeee920974d4c339eef4ef82d4f9aa7c8f83`;
- source registry: `sha256:9f295ea2970e24c4b88ffb0136c5c8cf7e5c48fbfd259db38bc895578d3a6813`.

## Consequences

- invocation is authorized as a future capability but has not occurred;
- retry remains forbidden after lease claim;
- scientific execution, [test-dataset access](../glossary_EN.md#term-test-dataset-access)
  to the test [dataset](../glossary_EN.md#term-dataset), and publication remain closed.

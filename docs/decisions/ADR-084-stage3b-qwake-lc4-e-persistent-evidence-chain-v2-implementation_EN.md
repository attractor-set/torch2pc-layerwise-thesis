# ADR-084: persistent evidence chain v2 implementation

- Status: accepted
- Date: 2026-07-30
- Scope: `QW-LC4-E`
- Base: PR #144 merge `3d092440b0314f02072c9773cc91018bf2860744`

## Context

ADR-083 defined the complete [evidence](../glossary_EN.md#term-evidence) chain, the prospective persistent lease
v2, and the mandatory durable terminal host-outcome receipt, while deliberately
leaving persistence unimplemented. Without a separate implementation, a future
[attempt](../glossary_EN.md#term-attempt) could again leave authorization and a negative outcome only in process
memory.

## Decision

Implement two narrow writer interfaces:

1. exclusive atomic persistence of the persistent [execution](../glossary_EN.md#term-execution) lease v2;
2. exclusive atomic persistence of the durable host-outcome receipt after
   verifying the exact bytes of the already-persisted lease.

Both writers use a temporary file in the target directory, mode `0600`, full
file `fsync`, atomic hard-link promotion without replacement, directory
`fsync`, and mandatory temporary-file cleanup. The parent directory chain must
already exist and must not contain symbolic links.

The lease writer fails closed when the output root, legacy lease, lease v2, or
outcome receipt already exists. The outcome writer fails closed when the lease
is absent or its exact canonical bytes differ. No collision may overwrite an
existing artifact.

## Boundary

The implementation is not wired into the host [runtime](../glossary_EN.md#term-runtime) invoker and is not called
by the current runtime operation. This slice does not inspect the image,
materialize a command, create a lease in the real output path, consume
authorization, spawn a child, or invoke Docker. Positive writer tests operate
only in isolated temporary repositories.

## Consequences

- `PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=true`;
- `DURABLE_OUTCOME_WRITER_IMPLEMENTED=true`;
- `LEASE_BOUND_HOST_INVOKER_ENFORCED=false`;
- `FINAL_EXECUTION_ACKNOWLEDGED=false`;
- `ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false`;
- actual runtime artifacts remain absent.

# ADR-117: attempt-003 host invocation command materialization authoring

## Status

Accepted as bounded authoring for exact host-command materialization. This slice
defines the future durable command record but does not persist it or spawn a
process.

## Context

PR #186 merged the authored host invocation chain into `main` as
`d63fca319436e530e8a8dbe8ce18fefa4ee70433`. Its contract identity is
`sha256:da89fd78683e01bdcfe85402b819a6c8e31ab3c496aa8ac9190f8d4480664191`
and [execution](../glossary_EN.md#term-execution) of the
[runtime](../glossary_EN.md#term-runtime) remains forbidden.

After that merge a dedicated composite future-invocation root was materialized:

- `experiments/frozen` is an exact frozen-tree copy with SHA-256
  `4b50d9d8ab3b085c8c965bbffd2249476ddb3e97f8a055533cb88d24b916dfd1`;
- `external/Torch2PC` is a clean checkout of
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- `results` is a new empty output namespace.

A host preflight then verified the resource profile, ROCm devices and immutable
image. The pure constructor built the future argv only in memory with identity
`sha256:fbac1c0e61b6f93395895f03dce5cb3e464e329b08990cdc8642149fff7feecd`.
No process, container, lease or [attempt](../glossary_EN.md#term-attempt) was
created.

A critical distinction is that
`claimed_at_utc=2026-08-10T04:03:59Z` belongs to the preflight observation. It
must not become the timestamp of the future real claim, because that would make
the durable lease assert a time before the actual transition.

## Decision

Add a pure command-materialization authoring contract, verifier and focused
tests. The contract freezes the preflight observation as
[evidence](../glossary_EN.md#term-evidence) while keeping it distinct from the
future authoritative command.

All static command fields are bound by a normalized command template with
SHA-256
`sha256:01fdd895e65ee59970e9a67c500ec4523e0039d468fe8e9553b0e4e2a53a7d89`.
Exactly one time value is replaced by
`__ATTEMPT003_CLAIMED_AT_UTC__`; every other argv element, environment value,
mount, image identity and host-resource binding must match the verified
preflight observation.

Future materialization must:

1. receive a new RFC3339 UTC-seconds `claimed_at_utc` at materialization time
   instead of reusing the preflight timestamp;
2. obtain a fresh exact `MaterializedHostInvocation` from the pure host-chain
   constructor;
3. prove the normalized template, image, environment, mounts and composite root
   are exact;
4. atomically persist exactly one record at
   `results/stage-3/qwake-lc4-runtime-validation-v1-attempt-003.host-invocation-command.json`;
5. spawn no process and execute no Docker operation.

## Boundary

This authoring slice does not materialize the authoritative command, persist a
command record, add a process spawner, execute Docker, consume authorization,
start the attempt, create a lease or outcome, invoke runtime or model code, or
access a [dataset](../glossary_EN.md#term-dataset).

Even after the separate command-materialization transition,
`runtime_execution_permitted=false` remains true. A later execution layer must
be authored and verified separately; no printed or preflight argv is execution
permission.

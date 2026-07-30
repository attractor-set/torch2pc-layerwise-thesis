# ADR-085: bind the host invoker to persistent lease v2

- **Status:** accepted
- **Date:** 2026-07-30

## Context

After ADR-084 the repository can atomically persist lease v2 and a durable
terminal outcome, while the historical host invoker can still be called without
verifying that lease. Historical frozen identities must remain unchanged.

## Decision

Add one prospective entry point, `invoke_lease_bound_host_runtime`. It:

1. verifies exact persisted lease-v2 bytes before image inspection or process
   access;
2. delegates at most one spawn to the unchanged historical invoker;
3. hashes complete streams independently from bounded capture;
4. persists exactly one durable terminal receipt for success, prelaunch
   rejection, spawn failure, and post-spawn failure;
5. rejects retry and fails closed when a receipt already exists;
6. supersedes the historical direct operation and requires a future
   authorization to name the lease-bound entry point.

A static verifier permits direct lower-level invocation only in the immutable
historical operation and this wiring module. New production call sites are
forbidden.

## Effect boundary

This slice does not create the production lease, inspect the local image,
materialize a command, or invoke Docker. Tests use temporary repositories, a
fake image, and a fake child process only.

```text
LEASE_BOUND_HOST_INVOKER_ENFORCED=true
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_PERFORMED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

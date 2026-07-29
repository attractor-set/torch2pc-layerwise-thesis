# ADR-075: `QW-LC4-E` one-shot host-runtime-invoker implementation

- **Status:** accepted
- **Date:** 2026-07-29
- **Scope:** `QW-LC4-E`, one-shot engineering invocation

## Context

ADR-074 froze the future host boundary for one container spawn while
intentionally leaving executable code absent. After verified merge of PR #135
into `main` `7f1655346bca77834d73a660c9857f1ff23b826c`, that boundary must be
implemented without invoking the [runtime](../glossary_EN.md#term-runtime) in the current slice.

## Decision

A separate implementation module is added. Importing the module is effect
free. Its explicitly called function:

1. revalidates the exact authoring contract and absence of the lease, output,
   and staging tree;
2. inspects the local immutable image twice;
3. materializes the canonical `docker run` argv twice and requires exact
   equality immediately before spawn;
4. creates at most one child through the sole `Popen`, with `shell=False`, a
   separate process group, and a fixed host environment;
5. forwards `SIGINT` and `SIGTERM`, applies a terminal timeout, and forbids
   automatic retry after the spawn [attempt](../glossary_EN.md#term-attempt);
6. bounds `stdout` and `stderr` capture to one MiB each and returns only an
   in-memory outcome without persisting the command or host logs.

The host never writes the [execution](../glossary_EN.md#term-execution) lease. Only the container entrypoint may
claim it atomically, in the same process that then revalidates admission and
invokes the bounded backend.

## Current-slice boundary

The invoker and exact `docker run` implementation are present, but branch-level
execution permission remains closed. The verifier does not call the effectful
API, and unit tests use only a fake child process. No lease, authorization
consumption, runtime execution, or output is therefore produced.

```text
HOST_RUNTIME_INVOKER_CONTRACT_PRESENT=true
HOST_RUNTIME_INVOKER_IMPLEMENTATION_PRESENT=true
HOST_RUNTIME_INVOKER_PRESENT=true
HOST_RUNTIME_INVOKER_EXECUTABLE=true
HOST_DOCKER_RUN_IMPLEMENTED=true
PRELAUNCH_IMAGE_INSPECTION_COUNT=2
PRELAUNCH_MATERIALIZATION_COUNT=2
SUBPROCESS_POPEN_CALL_LIMIT=1
EXACT_ARGV_ONLY=true
SHELL_INTERPRETATION_FORBIDDEN=true
ENVIRONMENT_INHERITANCE_FORBIDDEN=true
PROCESS_GROUP_REQUIRED=true
SIGNAL_FORWARDING_REQUIRED=true
BOUNDED_OUTPUT_CAPTURE_REQUIRED=true
AUTOMATIC_RETRY_AFTER_SPAWN_FORBIDDEN=true
HOST_EXECUTION_LEASE_WRITE_FORBIDDEN=true
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Consequences

A following slice may freeze the exact implementation in the repository and
separately prepare the single operator invocation. Merging ADR-075 itself does
not authorize execution or mutate the one-shot authorization.

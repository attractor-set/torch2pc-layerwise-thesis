# ADR-118: Attempt-003 host process-spawner implementation

## Status

Accepted as a bounded implementation slice. Base commit:
`34ec64823bff556706190c2f2c93b3a0653e293d`; base tree:
`b851597ba271cea6e0b2e5868a654cf5b52b43f2`.

## Context

PR #187 is merged into `main`. The authoritative host command has already been
materialized and independently reconstructed byte-for-byte. The following
identities are fixed:

- `claimed_at_utc=2026-08-10T14:47:42Z`;
- `invocation_sha256=sha256:91e762ba21c1d72b9282a3b0419206d5de1c3f88aac82a63dad76e27f0321c24`;
- `command_record_sha256=sha256:3ea2d34826fdd5846eee7cdfa84833f6b5e2293cfef76b76a51b64862cb143ca`;
- physical command-record SHA-256
  `f519d0821305171aa5c6ed05cad772f9fd85e93601fa1ec551e23058939d1ba6`.

The command record is the only admissible source of the future host spawn.
Authorization remains unconsumed, the
[attempt](../glossary_EN.md#term-attempt) has not started, and no
[execution](../glossary_EN.md#term-execution) lease,
[runtime](../glossary_EN.md#term-runtime) output, or host outcome exists.

## Decision

Implement the bounded host process spawner directly in this slice instead of
adding another intermediate contract-only PR.

The spawner must:

1. reverify the durable command record physical and semantic SHA immediately
   before spawn;
2. use only the persisted exact `argv`;
3. perform exactly one `subprocess.Popen`;
4. use `shell=False`;
5. use a fixed host environment (`LANG=C`, `LC_ALL=C`, fixed `PATH`) rather
   than inherit arbitrary host environment state;
6. use the execution root as `cwd`;
7. create a separate process group with `start_new_session=True`;
8. close unrelated file descriptors with `close_fds=True`;
9. forward `SIGINT` and `SIGTERM` to the child process group;
10. enforce a 7200-second timeout and a 30-second termination grace period;
11. bound `stdout` and `stderr` capture to one MiB each;
12. perform no automatic retry.

The implementation returns a terminal host outcome in memory but does not
persist it itself. Repository verification and tests never perform the real
spawn; dependency injection supplies a fake process adapter.

The host neither creates the execution lease nor consumes authorization. Those
transitions remain owned by
`container_entrypoint_atomic_execution_lease` inside the launched container.

## Slice boundary

After merge the implementation exists and is technically capable of executing
the exact persisted Docker command, but execution remains closed until a
separate explicit one-shot operator action.

```text
AUTHORITATIVE_HOST_COMMAND_MATERIALIZED=true
COMMAND_PERSISTED=true
PROCESS_SPAWNER_CONTRACT_PRESENT=true
HOST_PROCESS_SPAWNER_PRESENT=true
HOST_PROCESS_SPAWNER_EXECUTABLE=true
HOST_PROCESS_SPAWNED=false
DOCKER_RUN_IMPLEMENTED=true
DOCKER_RUN_INVOKED=false
AUTHORIZATION_USED=false
AUTHORIZATION_CONSUMED=false
ATTEMPT_STARTED=false
EXECUTION_LEASE_MATERIALIZED=false
RUNTIME_EXECUTION_PERMITTED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
MODEL_CODE_INVOKED=false
DATASET_ACCESSED=false
```

## Next transition

After CI, merge, and a read-only post-merge audit, only one substantive
transition remains: the explicit one-shot
[run](../glossary_EN.md#term-run). It reverifies the exact command record and
closed lease/output boundary, then invokes the merged
`spawn_attempt_003_persisted_command()` exactly once. After the host spawn, the
container entrypoint exclusively owns the atomic authorization claim and
consumption transition.

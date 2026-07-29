# ADR-074: QW-LC4-E one-shot host-runtime-invoker authoring

- Status: accepted for a separate authoring slice
- Date: 2026-07-29
- Base commit: `be6486a9e3670343132f2c863a5a0cd5969ee9f6`
- Related decisions: ADR-067, ADR-070, ADR-071, ADR-072, ADR-073

## Context

PR #134 materialized exact local-image inspection and the canonical argv for a
future container invocation. The host invoker remains absent. The next
contract must define the only permitted path from observation to
[execution](../glossary_EN.md#term-execution) without opening that path on the
authoring branch.

The existing one-shot entrypoint claims the persistent execution lease inside
the container and invokes the backend in the same process. A host-side lease
write would violate the already frozen claim-and-execute-same-process rule.

## Decision

Introduce the pure
`stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-contract-v1` contract. It
binds the PR #134 merge, wrapper-implementation package, one-shot invocation
authorization, exact image, container entrypoint, and atomic lease
implementation.

The contract freezes this sequence:

1. reverify unconsumed authorization and absence of repository effects;
2. inspect the exact image repo digest;
3. materialize the canonical argv in memory only;
4. immediately reinspect the image and compare a rebuilt argv while rechecking
   lease, output, and staging absence;
5. spawn exactly one child container process with argv and no shell;
6. let the container entrypoint claim the execution lease atomically;
7. revalidate the persistent lease and frozen admission after the claim;
8. invoke the bounded backend and promote complete output without replacement;
9. classify return code, timeout, or signal as a terminal outcome without
   automatic retry.

The host is forbidden to write the execution lease. Authorization is consumed
only at the successful atomic lease claim inside the same container process
that subsequently invokes the backend. Once present, the lease survives every
failure and prohibits retry.

## Process control

The future implementation must:

- pass an argv array and use `shell=false`;
- spawn at most one child per invoker call;
- reject arbitrary environment inheritance and working-directory overrides;
- create a separate child process group;
- forward `SIGINT` and `SIGTERM` to that group;
- enforce a 7200-second timeout and a 30-second graceful termination period;
- bound captured stdout and stderr to one MiB each;
- treat nonzero return, timeout, and signal outcomes as terminal;
- persist neither argv nor separate host logs;
- perform no automatic retry after a child-spawn [attempt](../glossary_EN.md#term-attempt).

The atomic lease remains the cross-process arbiter: competing containers cannot
both enter computation. Crash-safe one-shot enforcement begins at successful
persistent lease claim. A pre-claim failure does not consume authorization,
but one host-invoker instance still cannot perform a second spawn.

## Authoring boundary

This slice contains only a dataclass contract, verifier, frozen registry, tests,
and bilingual documentation. It imports neither `subprocess`, the [runtime](../glossary_EN.md#term-runtime)
backend, the execution-wrapper implementation, nor the command-materialization
implementation.

```text
HOST_RUNTIME_INVOKER_CONTRACT_PRESENT=true
HOST_RUNTIME_INVOKER_PRESENT=false
HOST_RUNTIME_INVOKER_EXECUTABLE=false
HOST_DOCKER_RUN_IMPLEMENTED=false
EXACT_ARGV_ONLY=true
SHELL_INTERPRETATION_FORBIDDEN=true
EXECUTION_ATTEMPT_LIMIT=1
HOST_EXECUTION_LEASE_WRITE_FORBIDDEN=true
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

After merge, a separate implementation branch may implement process control and
the single container spawn. Development and tests must not start the real
[runtime](../glossary_EN.md#term-runtime). The actual one-shot invocation
remains a distinct operation after independent implementation verification.

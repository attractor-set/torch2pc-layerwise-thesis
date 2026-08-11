# ADR-120: consolidated `QWake Attempt-004` execution chain

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-attempt-004-execution-chain-authoring-v1/contract.json -->

Normative terms:
[attempt](../glossary_EN.md#term-attempt),
[execution](../glossary_EN.md#term-execution),
[candidate](../glossary_EN.md#term-candidate),
[warm-up](../glossary_EN.md#term-warm-up),
[runtime](../glossary_EN.md#term-runtime),
[test-dataset access](../glossary_EN.md#term-test-dataset-access),
[evidence](../glossary_EN.md#term-evidence), and
[dataset](../glossary_EN.md#term-dataset).

## Decision

After canonical `main` is validated, the new attempt receives distinct
contract, lease, measurement-matrix backend, container entrypoint, and host
one-shot process-spawner identities. Historical Attempt-003 identities and
`stage3b_qwake_lc4_runtime_backend.py` are neither modified nor reused as
Attempt-004 effects.

The measurement backend injects `Attempt004CPUStabilizedMatrixExecutor` by
default. It fixes process affinity at logical CPU `0`, fixes PyTorch intra-op
and inter-op parallelism at `1`, executes fourteen discarded reserve-free
warm-up cells, and then delegates the unchanged measured matrix to the existing
`BoundedTorchMatrixExecutor`.

## One-shot boundary

The host operation:

1. verifies a clean source commit and unchanged Torch2PC and scientific
   authorization identities;
2. builds the image from the exact commit and captures its digest;
3. materializes a new Attempt-004 execution freeze;
4. materializes a distinct effective and unconsumed authorization;
5. persists the exact Docker argument vector before process creation;
6. invokes exactly one child process with `subprocess.Popen` and `shell=False`;
7. persists a durable host outcome regardless of the child-process result.

Automatic retry is forbidden after process creation is entered. The lease is
created only inside the container entrypoint and is the
authorization-consumption point.

## Immutable conditions

CPU primary measurements continue to use `time.process_time_ns()`. Twelve
measured repeats per candidate remain unchanged. The order-effect tolerance is
unchanged. Scientific execution, test-dataset access, and publication remain
closed.

## Boundary of this authoring

This ADR and its machine-readable contract only create the executable
Attempt-004 chain. The authoring commit performs no Docker invocation, creates
no authorization, materializes no lease, and starts no execution.

# ADR-069: bounded `QW-LC4-E` backend and one-shot entrypoint

[Русская версия](ADR-069-stage3b-qwake-lc4-e-runtime-backend-implementation.md)

- Status: accepted
- Date: 2026-07-28
- Scope: `QW-LC4-E`, engineering [execution](../glossary_EN.md#term-execution) of `LOCAL_COMPUTE`

## Context

After `ADR-068` was merged, the repository contained the atomic lease writer,
the no-replace result wrapper, and a machine-readable request for a future
execution freeze. It did not contain the concrete compute backend for the
registered `2 × 7 × 12` matrix and 28 exact-reserve probes, nor a one-shot
entrypoint. The generic executor was therefore insufficient to justify a lease
claim.

A synthetic CPU control exposed a numerical boundary. The completed upper
errors retained by `capture_fixedpred_frontier` differ from the algebraically
identical `fixed[index] - beliefs[index]` by about `1.4e-17..5.6e-17` in
`float64` for candidates `2..6`. The sealed `QW-LC4-I` implementation checks
that identity bitwise and consequently rejects a real state whose difference
is only floating-point roundoff. Rewriting the sealed `QW-LC4-I` module is not
permitted.

A twelve-repeat CPU control also showed that the empirical
`order_effect_passed` result may be false because timing and memory are
variable. Under `ADR-059`, this is an observed control result, not a reason to
discard a single [attempt](../glossary_EN.md#term-attempt) output after admission has been consumed.

## Decision

1. Add `stage3b_qwake_lc4_runtime_backend.py` as the concrete backend only for
   the frozen synthetic engineering domain: `lenet_classic`, FixedPred,
   `eta=1`, `stage2_baseline`, two registered lanes, seven candidates, twelve
   repeats, and 28 reserve probes.
2. Do not load a training or test [dataset](../glossary_EN.md#term-dataset). Inputs and targets come from a
   deterministic synthetic generator with the frozen seed.
3. Before capturing `opaque_state_ref`, canonicalize only already-completed
   upper-wavefront errors to `fixed - beliefs`, and only within the lane
   tolerance:
   - CPU `float64`: `atol=1e-12`, `rtol=1e-10`;
   - ROCm `float32`: `atol=1e-5`, `rtol=1e-4`.
4. Do not mutate the raw frontier. Record raw and canonical SHA-256 values,
   normalized indices, maximum defect, and tolerances. A defect outside the
   tolerance fails closed.
5. Both matched arms and reserve probes fork the same canonical
   `opaque_state_ref`. The `~R` comparison uses the responses from those same
   measured executions; it does not rerun either arm.
6. Matrix completeness, positions, identities, digests, cost schema, and all
   14 aggregates are integrity requirements. Empirical `~R`, RNG, reserve, and
   order-effect outcomes are retained as boolean results. A negative outcome
   produces `engineering_matrix_completed_validation_failed` while preserving
   the complete engineering [evidence](../glossary_EN.md#term-evidence).
7. Add `run_stage3b_qwake_lc4_authorized_runtime.py`. It verifies the future
   immutable `execution-freeze-v1` package, exact backend/entrypoint SHA-256,
   the Torch2PC commit, and image digests before any lease claim. Only then may
   it claim and execute in the same process.
8. The current slice does not contain `execution-freeze-v1` or an immutable
   image. The entrypoint must therefore stop before claiming a lease.
9. Materialize seven backend files only under the wrapper staging directory:
   report, 168 cell JSONL records, 28 probe JSONL records, aggregates,
   identities, backend receipt, and `SHA256SUMS`. Promotion remains the sealed
   wrapper's responsibility.

## Consequences

The backend and entrypoint become reviewable and synthetically testable. This
is not an image freeze, execution permission, lease claim, engineering result,
or scientific evidence. After merge, the only permitted next slice is the
separate immutable execution-freeze materialization bound to an exact commit
and image digest.

## Verifiable boundary

```text
qwake_adr=ADR-069-stage3b-qwake-lc4-e-runtime-backend-implementation
runtime_backend_branch_open=true
concrete_runtime_backend_present=true
one_shot_entrypoint_present=true
runtime_execution_freeze_guard_present=true
frontier_roundoff_canonicalization_present=true
raw_and_canonical_frontier_hashes_recorded=true
matched_matrix_authorized_cell_count=168
exact_reserve_probe_count=28
negative_validation_evidence_preserved=true
immutable_execution_image_present=false
execution_freeze_materialized=false
execution_lease_materialized=false
qw_lc4_e_execution_permitted=false
authorization_consumed=false
runtime_execution_started=false
runtime_execution_performed=false
engineering_evidence_present=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
local_compute_execution_open=false
```

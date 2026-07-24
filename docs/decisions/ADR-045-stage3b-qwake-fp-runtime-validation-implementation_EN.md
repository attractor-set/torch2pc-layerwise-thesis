# ADR-045: `QW-4B` runtime-validation admission and orchestration implementation

[Русская версия](ADR-045-stage3b-qwake-fp-runtime-validation-implementation.md)

- **Status:** accepted as `QW-4B-I`; [execution](../glossary_EN.md#term-execution) and the [evidence](../glossary_EN.md#term-evidence) run remain closed
- **Date:** 2026-07-24

```text
qwake_fp_runtime_validation_implementation_complete=true
qwake_fp_runtime_preflight_implemented=true
qwake_fp_runtime_authorization_validator_implemented=true
qwake_fp_runtime_adapter_symbols_bound=true
qwake_fp_matched_runtime_runner_implemented=true
qwake_fp_runtime_report_sealer_implemented=true
qwake_fp_canonical_torch_backend_implemented=true
qwake_fp_all_snapshot_observer_implemented=true
qwake_fp_authorized_execution_cli_implemented=true
qwake_fp_static_validation_receipt_chain_implemented=true
qwake_fp_runtime_authorization_issued=false
qwake_fp_runtime_validation_performed=false
qwake_fp_pre_freeze_evidence_generated=false
qwake_fp_pre_freeze_validation_complete=false
qwake_fp_live_adapters_bound=false
qwake_fp_scientific_image_freeze_permitted=false
qwake_fp_next_stage=QW-4-runtime-validation
qwake_fp_next_slice=QW-4-runtime-freeze
```

## Context

`QW-4A` froze the request, P0/P1/P2 pairs, equality fields, disabled-effect
counters, oracle isolation, and mandatory CPU/ROCm lanes. A real engineering
run still required a separate [runtime](../glossary_EN.md#term-runtime)
implementation that does not combine three different actions:

1. environment and source verification;
2. issuance of a single-run authorization;
3. execution and preservation of [evidence](../glossary_EN.md#term-evidence).

If implementation code can issue its own authorization or silently open
execution, the fail-closed boundary disappears. QW-4B is therefore separated
into implementation, freeze/authorization, and evidence slices.

## Decision

### 1. Non-computational preflight

`stage3b_qwake_fp_runtime.py` builds and revalidates
`stage3b-qwake-fp-runtime-preflight-v1`. The preflight binds:

- a clean source commit and canonical Git-index digest;
- a clean Torch2PC commit;
- the immutable image digest;
- QW-4A request and QW-2 contract SHA-256 values;
- the closed runtime-adapter-symbol registry digest;
- Python/PyTorch/HIP/device identities for both lanes;
- the ordered CPU/float64 then ROCm/float32 pair in one image.

Preflight permissions deny all effects and do not authorize execution.

### 2. Separate authorization schema

The implementation contains only a validator for a future
`stage3b-qwake-fp-runtime-authorization-v1`; it does not create or sign an
authorization package. Validation requires:

- the exact preflight digest;
- identical source/image/Torch2PC identity;
- the complete but engineering-only capability set;
- the SHA-256 of completed static/unit checks and a receipt chain binding it to the exact preflight;
- P0/P1/P2 on both CPU and ROCm lanes;
- one relative output root that was absent at issue time;
- exactly one [attempt](../glossary_EN.md#term-attempt);
- the exact operator acknowledgement;
- closed science, test-data, publication, and image-freeze gates.

Campaign data access, policy selection, confirmatory access, and publication
are outside the runtime-validation capability set.

### 3. Effect-local adapter boundary

`stage3b_qwake_fp_runtime_adapter.py` implements exactly the symbols frozen by
the QW-4A request:

```text
collect_A0
collect_A1
collect_A2
run_registered_analytics
compute_post_action_oracle
record_edge_costs
```

Every function checks its capability immediately before the effect. The module
has no import-time PyTorch/Torch2PC dependency and accepts only a backend object
from an authorized runtime session. A0 remains structural and cannot read
tensors, allocate temporary memory, synchronize a device, or perform D2H
transfer.

The concrete `stage3b_qwake_fp_runtime_torch.py` backend is already part of
this implementation slice. It hard-binds `lenet_classic`, corrected
`stage2_baseline` FixedPred, `eta=1`, the registered step count, and a
deterministic synthetic engineering batch. The instrumented arm uses an
equivalent copy of the frozen corrected FixedPred loop with a read-only
callback at snapshots `0..K`; the reference arm calls the original function
from the pinned Torch2PC checkout. Future P0/P1/P2 execution therefore tests
that callbacks preserve the [endpoint](../glossary_EN.md#term-endpoint), gradients, beliefs, loss, transitions, and
RNG state.

### 4. Matched runner

For every cell, the runner captures model/optimizer state and all RNG streams
once. It restores both before each arm. Arms execute sequentially in one of two
registered balanced orders:

```text
reference -> instrumented
instrumented -> reference
```

The runner checks authorization membership, state/RNG digests, lane, seed,
batch, and pair identity before applying the pure QW-4A comparators. Concurrent
execution of the two arms is not admitted.

### 5. Two-lane engineering report

The report must contain P0/P1/P2 for CPU and ROCm, per-lane nesting,
permission-negative audits, oracle isolation, and manifest/receipt/static
gates. ROCm pair results project onto the original `PreFreezeValidationReport`,
while CPU and ROCm remain explicit lane reports.

The report boundary is:

```text
engineering_evidence_only=true
scientific_evidence=false
publication_permitted=false
```

The pure sealer returns canonical JSON and SHA-256 without writing files.

### 6. CLI boundary

Three service CLIs are added:

- `preflight_stage3b_qwake_fp_runtime.py` builds or verifies a preflight;
- `verify_stage3b_qwake_fp_runtime_authorization.py` validates a future
  authorization, its static-validation receipt, and opens only an in-memory
  engineering session;
- `run_stage3b_qwake_fp_runtime_validation.py` is the only execution CLI and
  invokes FixedPred only after preflight, authorization, receipt-chain,
  source/image/Torch2PC identity, and absent-output-root checks pass. It writes
  the engineering-only report atomically and never opens scientific evidence
  or publication.

No CLI issues authorization. Preflight and verify do not invoke FixedPred; the
execution CLI fails closed without an externally frozen authorization.

## Implementation boundary

This slice completes QW-4B-I only. It does not contain:

- a frozen runtime preflight or authorization artifact;
- run seeds, batches, or an output root;
- actual CPU/ROCm execution or an issued authorization;
- runtime report files;
- permission to create scientific oracle labels;
- permission for QW-5 or C1/C2/C3/R.

The next QW-4B-F slice must freeze the actual preflight, exact cells,
image/source/Torch2PC identities, and single-run authorization. Only after that
merge may the QW-4B-E evidence run occur.

## Consequences

A green CI result means the admission, orchestration, and sealing contracts are
machine-checkable. It does not demonstrate hardware non-interference. Until a
successful sealed two-lane report exists,
`qwake_fp_scientific_image_freeze_permitted=false`.

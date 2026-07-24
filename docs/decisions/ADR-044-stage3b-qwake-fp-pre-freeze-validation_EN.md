# ADR-044: QWake-FP pre-freeze validation request and harness

[Russian version](ADR-044-stage3b-qwake-fp-pre-freeze-validation.md)

- **Status:** accepted as `QW-4A`; [execution](../glossary_EN.md#term-execution) remains closed
- **Date:** 2026-07-24

```text
qwake_fp_pre_freeze_validation_request_frozen=true
qwake_fp_pre_freeze_validation_request_id=stage3b-qwake-fp-pre-freeze-validation-v1
qwake_fp_pre_freeze_validation_harness_implemented=true
qwake_fp_pre_freeze_validation_complete=false
qwake_fp_runtime_authorization_issued=false
qwake_fp_pre_freeze_evidence_generated=false
qwake_fp_live_adapters_bound=false
qwake_fp_scientific_image_freeze_permitted=false
qwake_fp_next_stage=QW-4-runtime-validation
c1_collection_open=false
c2_calibration_open=false
c3_confirmatory_open=false
replication_open=false
```

## Context

`QW-1` froze the pure QWake core, `QW-2` froze the bounded `FixedPred` special
case, and `QW-3` implemented the backend-neutral superset pipeline. Before the
single scientific-image freeze, the project must verify that observation does
not perturb canonical computation, disabled capabilities produce zero effects,
the oracle remains post-action, and [observer cost](../glossary_EN.md#term-observer-cost)
is accounted for without duplication.

Coordination unit tests cannot replace validation on real computational paths.
Matched CPU/ROCm artifacts are required and do not yet exist. Therefore `QW-4`
is split only operationally, without changing the scientific plan:

- `QW-4A` — frozen request, schema, pure comparators, and fail-closed gates;
- `QW-4B` — separate [runtime](../glossary_EN.md#term-runtime) authorization,
  CPU/ROCm smoke, and a sealed engineering report.

Transition to `QW-5` is forbidden until `QW-4B` is complete.

## Decision

### 1. Frozen request

The canonical request is stored at:

```text
experiments/frozen/stage3b-qwake-fp-pre-freeze-validation-v1/request.json
```

It binds:

- the `stage3b-qwake-fp-special-case-v1` contract and SHA-256;
- the `cpu_float64_engineering` lane;
- the `rocm_float32_canonical` lane;
- matched pairs `P0`, `P1`, and `P2`;
- exact QW-2 equality and measurement fields;
- a closed future-runtime-adapter registry;
- the complete required gate set.

The request is neither authorization nor [evidence](../glossary_EN.md#term-evidence).

### 2. Matched pairs

For the same [model seed](../glossary_EN.md#term-model-seed), batch, initial
model/optimizer state, and RNG state, the runtime slice will execute
sequentially:

```text
P0: B0 <-> B0+A0
P1: B0 <-> B0+A0+A1
P2: B0 <-> B0+A0+A1+A2
```

SHA-256 identities are compared for:

- task-relative [endpoint](../glossary_EN.md#term-endpoint) response;
- named parameter gradients;
- endpoint beliefs;
- endpoint loss;
- transition sequence;
- RNG state after;
- snapshot identity.

The B0 reference arm has no observer effects or observer cost. The instrumented
arm must emit exactly the cumulative levels required by its pair.

### 3. Nested observations

The harness checks:

```text
A0(P0) = A0(P1) = A0(P2)
A1(P1) = A1(P2)
```

A more expensive level may not recompute or replace a previously acquired
payload.

### 4. Negative permission audit

For every disabled capability, the report records:

```text
invocation_count
tensor_read_count
temporary_allocation_count
synchronization_count
d2h_bytes
trace_bytes
output_count
```

Every value must be zero. Equal final scientific results alone do not prove the
absence of hidden overhead.

### 5. Oracle isolation

The oracle is created only after canonical action completion. Before that:

- oracle fields are absent from pre-action features;
- oracle-read count is zero;
- policy and observer have no oracle access;
- oracle creation ordinal is strictly greater than action-completion ordinal.

### 6. Cost

Observer host time maps exactly once to `observer_ns`.
[Device time](../glossary_EN.md#term-device-time) remains an auxiliary
measurement and is not added again. Temporary memory maps to the memory
component; D2H, synchronization, and trace remain explicit raw measurements.

### 7. Both lanes are mandatory

The CPU lane is an engineering control. The ROCm/float32 lane is canonical.
Image freeze may be proposed only after both smoke lanes, all three pairs,
nesting, negative audits, oracle isolation, manifest integrity, receipt-chain,
and static/unit gates pass.

## Implementation boundary

`QW-4A` implements only pure records and comparators. They:

- do not import PyTorch or Torch2PC runtime;
- do not execute FixedPred;
- do not read tensors;
- do not synchronize a device;
- do not generate oracle labels;
- do not write evidence;
- do not permit image freeze.

The canonical loader is registered as existing but unauthorized. Every
observer/oracle/cost runtime adapter remains `unbound_runtime_adapter`.

## Consequences

A passing `QW-4A` result means only that the request and validation harness are
deterministic and testable. It does not demonstrate non-interference on a real
CPU or ROCm device. That requires the separate `QW-4B` runtime slice and sealed
report.

Only `QW-5` image freeze may follow successful `QW-4B`. Scientific campaigns
`C1/C2/C3/R` remain closed.

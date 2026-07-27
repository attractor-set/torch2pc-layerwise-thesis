# ADR-064: fail-closed `QW-LC4-E` admission authoring

[Russian version](ADR-064-stage3b-qwake-lc4-e-execution-admission-authoring.md)

- **Status:** accepted as `QW-LC4-E` admission authoring;
  [execution](../glossary_EN.md#term-execution) has not started
- **Date:** July 27, 2026

## Context

`QW-LC4-F` completed after PR 124 was merged and merge commit
`453bb4eb6a20ae52a0d10384a1c54e45cf999143` was independently verified.
The frozen authorization permits one engineering
[attempt](../glossary_EN.md#term-attempt), but it must not start
[local compute](../glossary_EN.md#term-local-compute) by itself.

Three states must remain distinct:

1. authorization exists in the immutable package;
2. the control plane verified the conditions for consuming authorization;
3. model execution actually started.

Without a separate admission, authorization verification could be confused
with execution start or with engineering
[evidence](../glossary_EN.md#term-evidence).

## Decision

Add the pure `stage3b_qwake_lc4_execution_admission.py` schema and a validator
for a future admission. They:

- reverify the exact ten-file `QW-LC4-F` package;
- distinguish the control-plane merge commit from the immutable-image source
  commit;
- require the exact operator acknowledgement;
- require the result root and one-attempt lease to be absent;
- admit exactly one engineering attempt;
- preserve `runtime_execution_started=false`;
- keep scientific execution, test
  [dataset](../glossary_EN.md#term-dataset) access, and publication closed.

The schema does not import the model executor, create the result root, create
the lease, or write an admission record.

## Identities

```text
qwake_lc4_f_merge_commit=453bb4eb6a20ae52a0d10384a1c54e45cf999143
frozen_runtime_source_commit=51fc7537fdcb395145fc4c5a38b8918b018fe892
torch2pc_commit=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
image_digest=sha256:a31cf96e20ab45ce29fe18b68eb805bd048a02f1f8107cf680d1c174ea363929
preflight_sha256=sha256:3a8d7817338f3b93396270ea8e1b1b2fbda768dbd5461a18f97520948a53a9e6
authorization_sha256=sha256:d11b662a5c5eeada5333e69c6fddf2e50726c01b4d8c78a556a68167dbdd301e
authorized_output_root=results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001
```

## Boundaries

```text
QW_LC4_F_COMPLETE=true
QW_LC4_E_BRANCH_OPEN=true
EXECUTION_ADMISSION_IMPLEMENTED=true
EXECUTION_ADMISSION_ISSUED=false
QW_LC4_E_EXECUTION_PERMITTED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
```

## Consequences

A separate next slice must freeze a concrete admission record bound to the
exact control-plane commit. Only after independent verification may it add a
one-attempt lease and an execution wrapper.

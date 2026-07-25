# ADR-048: `QW-4B-E-v2` evidence and recovery adjudication

[Русская версия](ADR-048-stage3b-qwake-fp-runtime-validation-evidence-v2.md)

- Status: accepted
- Date: 25 July 2026

## Context

The single authorized [attempt](../glossary_EN.md#term-attempt) for
`QW-4B-E-v2` ran from an isolated checkout of source commit
`e413bb1e13cee42f702512e499f994e90df21e45` and Torch2PC
`b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` in the previously frozen
immutable image. The executor completed all six `CPU/ROCm × P0/P1/P2` cells,
created the exact six-file output, and sealed the engineering report.

After successful computation, the wrapper recorded the read-only audit status
incorrectly because it read `PIPESTATUS` after another command. The first
recovery audit then required raw-byte equality between equivalent JSON
serializations of the authorization. The second expected a nonexistent
`passed` field instead of checking `enabled=false` and a zero effect vector.
[Execution](../glossary_EN.md#term-execution) cannot be repeated because the
authorization is consumed.

## Decision

1. Preserve the exact output, the original failing completion receipt, and both
   failed recovery audits without rewriting them.
2. Admit the result as engineering [evidence](../glossary_EN.md#term-evidence)
   only after independent recovery-v3 verifies JSON and model equivalence,
   exact P0/P1/P2 cells, CPU/ROCm, observation nesting, oracle isolation, and
   zero effects for every disabled capability.
3. Freeze three separate layers: exact [runtime](../glossary_EN.md#term-runtime)
   output, complete
   provenance/adjudication package, and an external seal package.
4. Treat the authorization as permanently consumed; no retry is permitted.
5. Do not treat this report as scientific evidence and do not open publication,
   test access, or `QW-LC0` in this slice.

## Machine-checkable boundary

```text
qwake_qw4b_e_v2_runner_status=0
qwake_qw4b_e_v2_authorization_consumed=true
qwake_qw4b_e_v2_retry_permitted=false
qwake_qw4b_e_v2_runtime_rerun_performed=false
qwake_qw4b_e_v2_authorized_cell_count=6
qwake_qw4b_e_v2_cpu_lane_passed=true
qwake_qw4b_e_v2_rocm_lane_passed=true
qwake_qw4b_e_v2_engineering_evidence_present=true
qwake_qw4b_e_v2_image_freeze_eligible=true
qwake_qw4b_e_v2_scientific_evidence=false
qwake_qw4b_e_v2_publication_permitted=false
qwake_qw_lc0_open=false
```

## Consequences

Merging this slice completes the repository seal for the
[baseline](../glossary_EN.md#term-baseline) engineering
report. The next independent slice may only be `QW-LC0`, starting with its
semantics and scope boundary without retroactively changing `QW-4B-E-v2`.

# ADR-122: successful `QW-LC4-E` completion and transition to `QW-5`

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-lc4-e-attempt-005-success-transition-v1/receipt.json -->

Normative terms:
[attempt](../glossary_EN.md#term-attempt),
[execution](../glossary_EN.md#term-execution),
[run](../glossary_EN.md#term-run),
[runtime](../glossary_EN.md#term-runtime),
[evidence](../glossary_EN.md#term-evidence),
[freeze](../glossary_EN.md#term-freeze),
[test-dataset access](../glossary_EN.md#term-test-dataset-access), and
[dataset](../glossary_EN.md#term-dataset).

## Status

Accepted as the transition after successful engineering validation. This slice
does not execute `QW-5` and does not create the scientific image.

## Context

Attempt-005 was executed exactly once from tree
`170503e1f1be147be13c90f43c1012e8bb291b18` after ADR-121 was merged into
`main` `7168d6ebf3fbc27f5b85e1e44a7e8252f28038b0`. The external host run
created one child process, returned `return_code=0`, did not time out, and
performed no automatic retry. The one-shot authorization was consumed and
terminal runtime output is present.

The sealed engineering report has status
`engineering_matrix_completed_validation_passed`. It contains 168 authorized
measured cells, 28 reserve probes, and 14 paired aggregates. Response, RNG,
reserve-path, pair-completeness, and order-effect gates all passed
simultaneously. The CPU lane passed `7/7` aggregates and the ROCm lane passed
`7/7`; there are no order-effect failures.

This satisfies the previously frozen `QW-LC4-E report -> QW-5` boundary. The
result remains engineering evidence only: scientific execution, test-dataset
access, and publication are neither performed nor opened by this transition.

## Decision

1. Treat Attempt-005 as the terminal successful engineering-validation
   attempt; rerunning it is forbidden and unnecessary.
2. Materialize immutable transition receipt
   `stage3b-qwake-lc4-e-attempt-005-success-transition-v1`, binding the exact
   source, image, execution freeze, authorization, host command, lease, host
   outcome, runtime report, and execution receipts.
3. Mark `QW-LC4-E` complete: `QW_LC4_E_COMPLETE=true`.
4. Permit the next preregistered transition to `QW-5` and open only the
   scientific-image-freeze boundary:
   `QW5_TRANSITION_PERMITTED=true` and
   `QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=true`.
5. Do not materialize the scientific image in this slice:
   `QW5_IMAGE_FROZEN=false`.
6. Keep `C1/C2/C3/R`, scientific execution, test-dataset access, and
   publication closed until separate authorizations after the `QW-5` image
   receipt.
7. Do not modify terminal Attempt-003/004/005 evidence, algorithms, primary
   clocks, tolerances, paired ordering, or runtime implementation.

## Verifiable boundary

```text
ATTEMPT_005_TERMINAL=true
ATTEMPT_005_VALIDATION_PASSED=true
ATTEMPT_005_RETRY_PERMITTED=false
ATTEMPT_005_AUTHORIZED_CELL_COUNT=168
ATTEMPT_005_RESERVE_PROBE_COUNT=28
ATTEMPT_005_AGGREGATE_COUNT=14
ATTEMPT_005_CPU_ORDER_EFFECT_PASS_COUNT=7
ATTEMPT_005_ROCM_ORDER_EFFECT_PASS_COUNT=7
ATTEMPT_005_ORDER_EFFECT_FAILURE_COUNT=0
QW_LC4_E_COMPLETE=true
QW5_TRANSITION_PERMITTED=true
QW5_OPEN=true
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=true
QW5_IMAGE_FROZEN=false
SCIENTIFIC_EXECUTION_OPEN=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
RUNTIME_RERUN_PERFORMED=false
NEXT_SLICE=QW-5-scientific-image-freeze
```

## Consequences

The next permitted effect boundary is only the `QW-5` scientific-image freeze.
It must freeze the single scientific image for `C1/C2/C3/R`. The scientific
campaign remains closed until a materialized `QW-5` image receipt exists.

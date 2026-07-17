# Stage 3B B1/B2 matched profiling opening

[Русская версия](STAGE3B-B1-B2-MATCHED-PROFILING.md)

Status: **scientific admission open; execution not authorized**.

## Opening basis

Shared matched profiling opens only after two positive sealed decisions:

- `EQ-B1`: `isolated_layer_vjp` passed the registered structural, numerical,
  trajectory, observer, and provenance gates;
- `EQ-B2`: `composite_vjp` passed the corresponding gates, including direct
  B1/B2 comparison;
- both decisions have `status=pass`, `sealed=true`, and `failed_pairs=[]`.

The opening does not redefine the B1/B2 contracts and does not reinterpret
smoke evidence as runtime or memory evidence.

## Frozen matched matrix

The source 336-cell Stage 3B manifest is restricted to:

- `stage2_baseline`: 96 cells;
- `isolated_layer_vjp`: 96 cells;
- `composite_vjp`: 96 cells.

The resulting matrix has 288 cells, 144 each for `FixedPred` and `Strict`.
Source `block_id`, `cell_id`, dimensions, model seeds, and counterbalanced
candidate order are preserved. A0 `fixedpred_finite_step_control` is outside
this slice.

The protocol is inherited unchanged: 20 warm-up steps, 50 measured steps, and
5 repetitions; `model_seed` remains the independent unit.

## Open and closed work

Only scientific admission for a candidate-aware matched runner and a later
separate ROCm/float32 runtime freeze is open.

In this slice:

- no measurements are executed;
- no runtime authorization is issued;
- the test split remains closed;
- `full_stage3b_campaign_complete=false`;
- `EX-IF0`, the estimator, active `ECZ`, `QWake-PC`, controller actions, and
  offline policy selection remain closed.

Machine-readable manifest/request artifacts are produced by
`scripts/freeze_stage3b_matched_profiling.py` and must rebuild deterministically
under `--check`.

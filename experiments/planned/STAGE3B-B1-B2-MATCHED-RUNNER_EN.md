# Stage 3B B1/B2 matched runner contract

## Status

The candidate-aware runner contract is implemented for the scientifically
admitted 288-cell B0/B1/B2 matched matrix. Runtime authorization has not been
issued and measurements remain prohibited.

## Candidate dispatch

The runner freezes three lazy adapters:

- `stage2_baseline` → `torch2pc_thesis.pc_methods.load_pc_infer`;
- `isolated_layer_vjp` →
  `torch2pc_thesis.stage3b_b1_isolated_vjp.load_b1_pc_infer`;
- `composite_vjp` →
  `torch2pc_thesis.stage3b_b2_composite_vjp.load_b2_pc_infer`.

The planner validates the committed matched manifest and opening request,
requires all 96 blocks and 288 cells, preserves source `block_order` and
`candidate_order`, and maps `fixedpred`/`strict` to the existing Torch2PC
method labels.

## Reset and order contract

Before every candidate in a matched block, the future runtime executor must
restore:

1. model state;
2. optimizer state;
3. RNG state;
4. the frozen minibatch state.

The contract is represented as
`restore_model_optimizer_rng_and_minibatch_before_each_candidate`. A mocked
block harness tests restoration and dispatch order without creating timing,
memory, gradient, or other profiling evidence.

## Current boundary

Every planned cell has disposition `blocked_runtime_authorization`.
The planner can write only a non-evidence plan under `/tmp`.

This slice does not:

- issue ROCm/float32 runtime authorization;
- execute warm-up or measured steps;
- write profiling results;
- change sealed B1/B2 evidence or contracts;
- open EX-IF0, estimator, active ECZ, QWake-PC, controller actions, offline
  policy selection, or test-split access.

The next separate slice is the ROCm/float32 project/environment freeze,
lane preflight, operator acknowledgement, and authorization-token contract.

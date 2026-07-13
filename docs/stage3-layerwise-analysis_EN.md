# Stage 3: layer-wise diagnostic path

## Purpose

This path adds two validation-only studies:

1. **Same-state gradient probe**: BP, Exact, FixedPred, and Strict receive one checkpoint and identical validation batches. No optimizer step is applied. Gradients are compared by parameter and top-level layer.
2. **Representation probe**: independently trained checkpoints are evaluated on one fixed validation sample set using linear CKA, RSA, and a full cross-layer CKA matrix.

Hooks and tensor copies invalidate timing and memory measurements from these runs. Stage 1/2 remain unchanged; all new observations belong to Stage 3.

## Installation check

```bash
python -m pytest tests/unit/test_layerwise.py
python -m ruff check \
  src/torch2pc_thesis/layerwise.py \
  scripts/run_stage3_same_state_probe.py \
  scripts/run_stage3_representation_probe.py \
  scripts/aggregate_stage3_layerwise.py \
  tests/unit/test_layerwise.py
```

## Locate checkpoints

```bash
find results -type f -name 'checkpoint.pt' | sort
```

Stage 1/2 checkpoints are distributed in the replication bundle rather than tracked in Git. Use the paired BP checkpoint as the canonical same-state starting point.

## Same-state gradient probe

```bash
python scripts/run_stage3_same_state_probe.py \
  --checkpoint /absolute/path/to/checkpoint.pt \
  --checkpoint-label final \
  --output results/stage3/layerwise/pilot/seed-0/final \
  --enforce-exact-control
```

Outputs: `gradient_metrics.csv`, `gradient_summary.csv`, `method_losses.csv`, and `metadata.json`.

## Representation probe

```bash
python scripts/run_stage3_representation_probe.py \
  --checkpoint bp=/path/to/bp/checkpoint.pt \
  --checkpoint exact=/path/to/exact/checkpoint.pt \
  --checkpoint fixedpred=/path/to/fixedpred/checkpoint.pt \
  --checkpoint strict=/path/to/strict/checkpoint.pt \
  --output results/stage3/layerwise/pilot/seed-0/final
```

Outputs: `representation_metrics.csv`, `cross_layer_cka.csv`, compressed activation matrices, and `metadata.json`.

## Aggregate seeds

```bash
python scripts/aggregate_stage3_layerwise.py \
  --root results/stage3/layerwise/pilot \
  --output results/stage3/layerwise/pilot/combined
```

Aggregate probe batches within each model seed before paired inference across seeds. Layers and batches are not independent replicas.

## Limitation

This version analyzes available checkpoints and final PC gradients. It does not reconstruct missing Stage 1/2 intermediate checkpoints or capture each internal Torch2PC inference iteration. Those extensions belong to separate Stage 3 training and Torch2PC instrumentation patches after the observation schema is frozen.

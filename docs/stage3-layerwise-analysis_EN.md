# Stage 3: layer-wise diagnostic path

[Русская версия](stage3-layerwise-analysis.md)

## Purpose

This path adds two validation-only studies:

1. **Same-state gradient probe** — BP, Exact, FixedPred, and Strict receive one
   [checkpoint](glossary_EN.md#term-checkpoint) and the same validation batch. No optimizer step is applied.
   Gradients are compared separately by parameter and top-level layer.
2. **Representation probe** — independently trained checkpoints are compared
   on one fixed validation-example set using linear CKA, RSA, and a complete
   cross-layer CKA matrix.

Diagnostic runs use hooks and tensor copies, so their time and memory
measurements are not reference performance measurements. Stages 1 and 2 remain
unchanged; all new observations belong to Stage 3.

## 1. Installation check

```bash
python -m pytest tests/unit/test_layerwise.py
python -m ruff check \
  src/torch2pc_thesis/layerwise.py \
  scripts/run_stage3_same_state_probe.py \
  scripts/run_stage3_representation_probe.py \
  scripts/aggregate_stage3_layerwise.py \
  tests/unit/test_layerwise.py
```

## 2. Locate a checkpoint

Stage 1 and Stage 2 checkpoints are not tracked in Git. Use an unpacked
replication bundle or local artifacts. Use the paired BP [checkpoint](glossary_EN.md#term-checkpoint) as the
canonical same-state starting point:

```bash
find results -type f -name 'checkpoint.pt' | sort
```

## 3. Same-state gradient probe

```bash
python scripts/run_stage3_same_state_probe.py \
  --checkpoint /absolute/path/to/checkpoint.pt \
  --checkpoint-label final \
  --output results/stage3/layerwise/pilot/seed-0/final \
  --enforce-exact-control
```

Outputs:

- `gradient_metrics.csv` — one row per batch, method, scope, and
  layer/parameter;
- `gradient_summary.csv` — mean across diagnostic batches within one model;
- `method_losses.csv` — diagnostic method loss;
- `metadata.json` — [dataset](glossary_EN.md#term-dataset), model, seed, validation-index hash, and the
  Exact-versus-BP control result.

Primary fields:

- `cosine` — direction agreement;
- `relative_l2` — relative error of the full vector;
- `norm_ratio` — predictive-coding gradient norm divided by the BP norm;
- `sign_agreement` — fraction of matching signs;
- `max_abs_difference` — maximum absolute difference.

An independently trained model remains the [independent statistical unit](glossary_EN.md#term-statistical-unit). Rows
from different layers and batches are not independent replications.

## 4. Representation probe

For a valid comparison, checkpoints must share the [dataset](glossary_EN.md#term-dataset), model, split seed,
and validation fraction.

```bash
python scripts/run_stage3_representation_probe.py \
  --checkpoint bp=/path/to/bp/checkpoint.pt \
  --checkpoint exact=/path/to/exact/checkpoint.pt \
  --checkpoint fixedpred=/path/to/fixedpred/checkpoint.pt \
  --checkpoint strict=/path/to/strict/checkpoint.pt \
  --output results/stage3/layerwise/pilot/seed-0/final
```

Outputs:

- `representation_metrics.csv` — CKA and RSA for corresponding layers;
- `cross_layer_cka.csv` — complete “BP layer × [candidate](glossary_EN.md#term-candidate) layer” matrix;
- `activations_<label>.npz` — example-aligned activation matrices;
- `metadata.json` — [checkpoint](glossary_EN.md#term-checkpoint) list, layers, and validation-index hash.

Layers `0`, `1`, `3`, `4`, and `5` correspond to the top-level blocks of the
current `lenet_classic`. If the model changes, freeze the layer list in a
separate Stage 3 [configuration](glossary_EN.md#term-configuration) before confirmatory [execution](glossary_EN.md#term-execution).

## 5. Aggregate multiple models

Organize artifacts by seed and [checkpoint](glossary_EN.md#term-checkpoint), then run:

```bash
python scripts/aggregate_stage3_layerwise.py \
  --root results/stage3/layerwise/pilot \
  --output results/stage3/layerwise/pilot/combined
```

The script combines tables but intentionally performs no statistical test.
Aggregate diagnostic batches within each model first, then perform paired
analysis across independently trained models.

## 6. Recommended pilot study

- [dataset](glossary_EN.md#term-dataset): FashionMNIST;
- model: `lenet_classic`;
- independently trained models: 3;
- same-state probe batches: 5;
- representation-probe examples: 1000;
- [checkpoint](glossary_EN.md#term-checkpoint): best final checkpoint;
- test-data loader: not constructed.

After checking data volume, Exact-control stability, and the absence of
degenerate CKA, freeze:

- layers;
- checkpoints;
- batch and example counts;
- hypothesis families;
- numerical-equivalence thresholds;
- invalid-observation exclusion rules.

## 7. First-version limitation

The patch analyzes available checkpoints and final predictive-coding
gradients. It does not reconstruct missing intermediate Stage 1/2 checkpoints
or extract states after every internal Torch2PC inference iteration.

For trajectory analysis, create a separate Stage 3 training campaign that
stores checkpoints at prespecified optimizer-update fractions. Add per-step
inference traces through a separate Torch2PC instrumentation patch after the
observation schema is frozen, so diagnostic correctness is not conflated with
a change to the predictive-coding [execution](glossary_EN.md#term-execution) path.

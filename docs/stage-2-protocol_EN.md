# Final Stage 2 protocol

Final Stage 2 is an exact replication of the completed 80-cell confirmatory
matrix with one controlled intervention: the Torch2PC implementation revision.

## Fixed factors

- datasets: MNIST and FashionMNIST;
- architecture: `lenet_classic`;
- methods: BP, Exact, FixedPred, and Strict;
- model seeds: 0 through 9;
- deterministic train/validation/test split files and their SHA-256 digests;
- optimizer, learning rate, batch size, epochs, dtype, execution-order policy,
  container runtime, PyTorch/ROCm stack, and target hardware;
- FixedPred: `eta=0.1`, `inference_steps=10`;
- Strict: `eta=0.05`, `inference_steps=20`.

## Controlled intervention

Stage 1 uses the original Torch2PC revision
`00c6c50ee3540537bbb56ab2b6567b541f42b093`. Stage 2 uses a separately pinned
candidate revision derived from that commit. The candidate commit must be a
full Git SHA and must differ from the Stage 1 revision.

## Isolation

Stage 2 writes to its own registry, run directory, summaries, tables,
environment lock, control gates, execution plan, and freeze manifest. Stage 1
artifacts are read-only reference evidence.

## Required gates

Before the 80-cell matrix can run, both CPU and GPU gates must pass:

1. patched Exact versus backpropagation;
2. patched control FixedPred versus patched Exact;
3. original versus patched loss, output derivative, beliefs, prediction
   errors, and parameter gradients for Exact, FixedPred, and Strict;
4. candidate and reference worktrees match their pinned commits;
5. the Stage 2 image, prepared assets, environment lock, execution plan, and
   freeze manifest refer to the same source and Torch2PC revisions.

## Primary comparison

The cross-version analysis is paired by dataset, model, method, and model seed.
It reports absolute timing and memory changes, method-to-BP slowdown ratios,
quality differences, and difference-in-differences contrasts. Stage 2 does not
replace or regenerate Stage 1 evidence.

## Evidence commit model

The Docker image is built from a clean execution commit. The local
`prepared_assets.json` is generated as an ignored file and is referenced by its
SHA-256 digest in the environment lock. After the environment lock, CPU/GPU
gates, and execution plan are generated, those evidence files are committed
without changing any locked source or configuration file. The freeze manifest
is committed in the next evidence commit. Before matrix execution, the protocol
gate verifies that the current branch descends from the execution commit and
that every locked source/configuration file still matches the environment lock.

After all 80 runs complete, `prepared_assets.json`, the Stage 2 registry,
summaries, tables, and manifests are added in the final evidence commit. This
keeps the Docker image tied to the execution commit while allowing generated
research evidence to be versioned without a cyclic environment-lock rebuild.

## Matrix closure

After execution, `make snapshot-stage2` verifies exactly 80 unique successful
cells, test evaluation for every cell, single source and Torch2PC revisions,
40/40 dataset counts, and 20/20/20/20 method counts. It creates an immutable
registry snapshot, SHA-256 record, and completion summary. Stage 2 reports and
the cross-version analysis are built from that snapshot.

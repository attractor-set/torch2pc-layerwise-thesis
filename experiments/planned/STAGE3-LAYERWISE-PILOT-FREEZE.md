# Stage 3 Layer-wise Pilot Freeze

## Scope

- Dataset: FashionMNIST
- Architecture: lenet_classic
- Pilot model seeds: 0, 1, 2
- Methods: BP, Exact, FixedPred, Strict
- Checkpoint: final
- Same-state reference checkpoint: BP checkpoint of the paired seed
- Representation comparison: independently trained paired checkpoints
- Execution environment: controlled ROCm Docker image

## Frozen observations

- Gradient cosine similarity
- Gradient relative L2
- Gradient norm ratio
- Gradient sign agreement
- Linear CKA
- RSA
- Cross-layer CKA

## Statistical unit

The independently trained model seed is the statistical unit.
Layers, parameters, batches, and samples are repeated observations within a seed.

## Confirmatory plan

- Primary dataset: FashionMNIST
- Model seeds: 0–9
- Same-state analysis for all seeds
- Representation analysis for all seeds
- Exact–BP numerical control required for every seed
- Holm correction within predefined metric families
- Raw diagnostic artifacts remain local
- Aggregated summaries and manifests may be versioned

## Freeze rule

Metric definitions, layer selection, checkpoint selection, sample selection,
and numerical gates must not be changed after confirmatory execution starts.

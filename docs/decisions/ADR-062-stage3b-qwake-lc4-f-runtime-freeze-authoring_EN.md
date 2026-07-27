# ADR-062: `QW-LC4-F` runtime-freeze authoring

[Russian version](ADR-062-stage3b-qwake-lc4-f-runtime-freeze-authoring.md)

- Status: accepted
- Date: July 27, 2026

## Context

After the bounded `QW-LC4-I` implementation merged and was independently
verified, [runtime](../glossary_EN.md#term-runtime)-freeze authoring is
permitted but mechanism [execution](../glossary_EN.md#term-execution) is not.
The future engineering [attempt](../glossary_EN.md#term-attempt) must bind one
immutable source commit, one image, the exact Torch2PC checkout, the
`QW-LC4-I` implementation, the `QW-LC3` contract, two runtime lanes, every
[candidate](../glossary_EN.md#term-candidate) index, and one attempt only.

The image digest cannot be validly frozen before the commit containing the
runtime adapter and admission schemas exists. `QW-LC4-F` is therefore split
into two ordered actions on the same branch:

1. materialize and verify authoring code plus the frozen request;
2. commit that authoring state, build the image from that commit, then
   materialize the actual preflight, authorization, and receipt artifacts.

## Decision

### 1. Frozen request

Request `stage3b-qwake-lc4-f-runtime-freeze-request-v1` freezes:

- `FixedPred`, `eta=1`, `lenet_classic`, and `stage2_baseline`;
- candidate indices `0..6`;
- `cpu_float64_engineering` and `rocm_float32_canonical` lanes;
- twelve balanced repeats for every lane/candidate combination;
- two exact reserve probes for every such combination;
- [model seed](../glossary_EN.md#term-model-seed) `0` and the synthetic
  engineering batch;
- exactly one future engineering attempt;
- a dedicated output root;
- no [dataset](../glossary_EN.md#term-dataset), scientific execution,
  publication, or policy activation.

The resulting matrix contains 14 runtime cells, 168 matched-pair cells, and 28
reserve probes. No matrix element is executed in this slice.

### 2. Runtime adapter

`RuntimeFrontierAdapter` accepts an already captured FixedPred state and only
adapts it to `FixedPredFrontier` plus an immutable `opaque_state_ref`. It:

- requires the six top-level `lenet_classic` blocks;
- validates lane device and dtype;
- requires the registered seed and batch id;
- does not run the model;
- does not load a dataset;
- does not write results;
- does not expose a scientific executor.

### 3. Preflight

The preflight binds:

- a clean source commit;
- the complete tracked-source index;
- the Torch2PC commit;
- image and repository digests;
- the `QW-LC4-F` request;
- `QW-LC4-I` source, manifest, and registry;
- the `QW-LC3` contract and registry;
- the ordered adapter registry;
- CPU and ROCm runtime probes;
- clock and memory sources;
- absence of the output root.

The preflight is always deny-all and contains no execution permission.

### 4. Authorization

After exact preflight verification, a separate authorization object may permit
one engineering attempt and only the complete registered action set. It
contains 168 exact repeat cells. Authorization is not execution:

- `runtime_execution_performed=false`;
- `engineering_evidence_present=false`;
- `scientific_execution_open=false`;
- `test_dataset_access=false`;
- `publication_permitted=false`;
- `image_freeze_permitted=false`.

### 5. Final freeze

After the authoring slice is committed, an immutable image is built from that
commit. Only the actual image digest, live runtime probes, static validation
log, and receipt may enter
`stage3b-qwake-lc4-f-runtime-freeze-v1`.

The sealing script refuses overwrite, revalidates preflight and authorization,
and does not call a runtime executor.

## Consequences

- `QW-LC4-I` is complete.
- `QW-LC4-F` authoring is materialized.
- `QW-LC4-F` itself is not yet materialized or complete.
- `QW-LC4-E` remains closed.
- Runtime execution, feature collection, oracle labels, the test dataset, and
  publication remain closed.
- The image digest is not guessed; it will be obtained only from the authoring
  commit image build.

## Verifiable flags

```text
qwake_qw_lc4_i_complete=true
qwake_qw_lc4_f_authoring_open=true
qwake_qw_lc4_f_authoring_materialized=true
qwake_qw_lc4_f_request_frozen=true
qwake_qw_lc4_f_materialized=false
qwake_qw_lc4_f_complete=false
qwake_qw_lc4_e_branch_permitted=false
qwake_local_compute_execution_open=false
feature_collection_permitted=false
oracle_label_generation_open=false
policy_activation_permitted=false
scientific_execution_open=false
test_dataset_access=false
publication_permitted=false
runtime_rerun_performed=false
```

# Torch2PC `patched-v1`: implementation changes and mathematical-equivalence rationale

[Русская версия](torch2pc-patched-v1-equivalence.md)

## 1. Purpose

This document describes the changes made to the Torch2PC implementation for final Stage 2 and explains why they:

1. preserve the mathematical definitions of the studied methods;
2. preserve computed states and gradients within the registered experimental scope;
3. apply to the [architecture](glossary_EN.md#term-architecture), data, and protocol of `torch2pc-layerwise-thesis`;
4. primarily change the computational path, the number of repeated automatic-differentiation graph traversals, and related overhead.

The document does not claim universal formal equivalence for every possible PyTorch module. Its conclusion is limited to pinned source versions, the controlled environment, and the model class tested in the experiment.

## 2. Compared implementation identities

| Role | Repository or artifact | Commit or SHA-256 |
|---|---|---|
| Original Stage 1 implementation | `external/Torch2PC-original` | `00c6c50ee3540537bbb56ab2b6567b541f42b093` |
| Patched Stage 2 implementation | `external/Torch2PC` | `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |
| Cumulative patch | `patches/torch2pc-patched-v1.patch` | `7ea8733d3f8f8c39251e453cf1631cd0e75b8b42da6da1e67053bebdc9f692b3` |
| Stage 2 [execution](glossary_EN.md#term-execution)-source commit | main repository | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Environment lock | `results/stage-2/summaries/environment-lock.json` | `0ffe23c915ee47a38d1aaa3d2eb5b8175ca8e63be25840380b19fc6bdd2b045b` |

Stage 2 repeats the Stage 1 matrix:

```text
2 datasets × 1 model × 4 methods × 10 seeds = 80 cells
```

The controlled intervention is limited to the Torch2PC commit. Datasets, splits, model, methods, training parameters, random seeds, epochs, batch size, container image, hardware platform, and analysis rules remain fixed according to the Stage 2 protocol and environment lock.

## 3. Mathematical invariants

The patch preserves the definitions and computation order that are material to the studied methods.

### 3.1. Forward model and loss function

The patch does not change:

- the composition and order of `torch.nn.Sequential` layers;
- layer functions;
- model parameters;
- the loss function;
- input and target tensors;
- the optimizer or parameter-update rules used in the thesis project.

The model’s forward mapping and optimized objective therefore remain unchanged.

### 3.2. Exact

Exact preserves the relation between feed-forward activation, error, and belief:

```text
belief = activation - epsilon
```

The change combines repeated computation into one forward pass and one coordinated reverse traversal. It computes the derivative of the same function with respect to the same activations and parameter tensors. The organization of automatic-differentiation calls changes; the differentiated expression does not.

### 3.3. FixedPred

FixedPred preserves:

```text
epsilon = fixed_activation - belief
state update = epsilon - VJP(next_error)
```

The linearization point remains fixed throughout [state inference](glossary_EN.md#term-state-inference). The patch constructs local VJP graphs once at that point and reuses them across inference steps. This removes repeated construction of equivalent graphs while preserving the Jacobian to which the [vector–Jacobian product](glossary_EN.md#term-vjp) is applied.

### 3.4. Strict

Strict preserves:

```text
epsilon = local_prediction - belief
state update = epsilon - VJP(next_error)
```

Errors are recomputed at every inference step, and updates retain their original reverse order. The patch reuses the output of an already completed local forward pass only within the same iteration; it does not carry a prediction across inference steps.

### 3.5. Parameter gradients

Before the patch, individual parameters of one module could be differentiated through several separate `torch.autograd.grad` calls. After the patch, the module parameters are passed to one call.

For parameters \(\theta_1,\ldots,\theta_k\), the transformation changes:

```text
grad(y, theta_1), ..., grad(y, theta_k)
```

to:

```text
grad(y, (theta_1, ..., theta_k))
```

Both forms compute components of the same derivative \(\partial y / \partial \theta\). The grouped call reduces reverse traversals without changing the function, differentiation variables, or VJP input vector.

## 4. Detailed implementation changes

### 4.1. API correctness and input reuse

The patch:

- passes a user-provided `vinit` value to Strict;
- correctly reuses prepared Exact activations and loss;
- replaces `== None` checks with `is None`.

Stage 1 and Stage 2 experiment configurations use `vinit=None`. Correct handling of an explicit `vinit` therefore broadens API correctness without changing the studied [execution](glossary_EN.md#term-execution) path.

### 4.2. Grouped parameter VJP computation

The patch:

- computes gradients for all trainable parameters of one sequential module together;
- skips parameterless modules;
- releases the local graph after the required VJP completes.

It preserves:

- the tensors with respect to which derivatives are taken;
- the scalar or vector output;
- the `grad_outputs` argument;
- the mapping from each gradient to its parameter.

### 4.3. Single-pass Exact

The patch:

- uses one forward pass;
- extracts activation errors and parameter gradients through one coordinated reverse traversal;
- removes a repeated forward pass and a sequence of separate reverse traversals.

Activation values, loss, the differentiated graph, and resulting derivatives are preserved.

### 4.4. VJP reuse in FixedPred

The patch:

- creates the local graph once at the fixed linearization point;
- reapplies the pullback over `n` state-inference steps;
- releases the graph after its final use;
- applies `detach()` where computational history must be separated and avoids an independent storage copy when the method does not require one.

The fixed prediction, Jacobian at the linearization point, and state-update sequence are preserved.

### 4.5. Local-forward reuse in Strict

The patch:

- uses one local-forward output for both the [prediction error](glossary_EN.md#term-prediction-error) and the VJP of the same iteration;
- removes redundant `model.zero_grad()` calls inside [state inference](glossary_EN.md#term-state-inference);
- reduces clone and copy operations;
- preserves a new forward pass at every inference step and the original reverse-order update.

`torch.autograd.grad` returns gradients without accumulating them in parameter `.grad` fields. Removing `zero_grad()` from this internal path therefore does not change the computed VJP.

### 4.6. Tests and microbenchmark

The [candidate](glossary_EN.md#term-candidate) adds:

- original-versus-patched equivalence tests;
- a patched Exact-versus-BP test;
- an explicit-`vinit` regression test;
- a CPU/GPU-compatible microbenchmark.

The [candidate](glossary_EN.md#term-candidate)’s local test suite reports:

```text
5 passed
```

The microbenchmark is diagnostic. Scientific [runtime](glossary_EN.md#term-runtime) conclusions use the complete paired Stage 1/Stage 2 matrix.

## 5. Structural evidence of algorithm preservation

An automated structural check of the pinned [candidate](glossary_EN.md#term-candidate) source confirms that:

- Strict recomputes errors at every iteration;
- Strict uses `prediction - belief`;
- the Strict update has the form `epsilon - VJP`;
- FixedPred uses `activation - belief`;
- the FixedPred update has the form `epsilon - VJP`;
- Exact uses `activation - epsilon`.

All structural observations are `true` in the CPU and GPU control artifacts:

```text
results/stage-2/summaries/control_gate_cpu.json
results/stage-2/summaries/control_gate_gpu.json
```

The structural check shows that the key formulas and algorithm order remain present in the [candidate](glossary_EN.md#term-candidate) source. Numerical comparison of states and gradients complements this [evidence](glossary_EN.md#term-evidence).

## 6. Numerical evidence

Controls were run for model seeds `0, 1, 2`: three batches for internal controls and one cross-version batch per seed. The comparisons cover loss, output derivative, beliefs, `epsilon`, and parameter gradients.

### 6.1. CPU, float64

Preregistered thresholds:

```text
minimum cosine similarity = 0.99999
maximum relative L2       = 1e-7
```

Results:

| Control | Minimum [cosine similarity](glossary_EN.md#term-cosine-similarity) | Maximum relative L2 | Maximum absolute difference |
|---|---:|---:|---:|
| Patched Exact versus BP | `0.999999999999997` | `0.0` | `0.0` |
| Patched FixedPred control versus Exact | `0.9999999999999962` | `1.0959254353588235e-12` | `6.5910818469738786e-15` |
| Original versus patched Exact | `0.9999999999999951` | `0.0` | `0.0` |
| Original versus patched FixedPred | `0.9999999999999949` | `0.0` | `0.0` |
| Original versus patched Strict | `0.9999999999999901` | `0.0` | `0.0` |

Outcome:

```text
gate_observed_within_thresholds = true
```

For direct original-versus-patched comparisons, maximum relative-L2 and absolute differences are zero in the tested CPU/float64 scope.

### 6.2. GPU, float32, ROCm

Preregistered thresholds:

```text
minimum cosine similarity = 0.999
maximum relative L2       = 0.001
```

Results:

| Control | Minimum [cosine similarity](glossary_EN.md#term-cosine-similarity) | Maximum relative L2 | Maximum absolute difference |
|---|---:|---:|---:|
| Patched Exact versus BP | `0.999999463558197` | `0.0` | `0.0` |
| Patched FixedPred control versus Exact | `0.9999996423721313` | `0.0009624222213572001` | `2.0605511963367462e-06` |
| Original versus patched Exact | `0.9999997019767761` | `0.0` | `0.0` |
| Original versus patched FixedPred | `0.9999905228614807` | `0.0` | `0.0` |
| Original versus patched Strict | `0.9999954104423523` | `0.0` | `0.0` |

Outcome:

```text
gate_observed_within_thresholds = true
```

The nonzero FixedPred-versus-Exact difference compares two methods in float32 and remains within the preregistered tolerance. For direct original-versus-patched Exact, FixedPred, and Strict comparisons, maximum relative-L2 and absolute differences are zero in the tested GPU scope.

## 7. Why the evidence is sufficient for this experiment

Stage 2 uses:

- `lenet_classic`;
- MNIST and FashionMNIST;
- BP, Exact, FixedPred, and Strict;
- seeds `0..9`;
- the same [dataset](glossary_EN.md#term-dataset) splits;
- the same method hyperparameters;
- the same training pipeline;
- a pinned PyTorch/ROCm image;
- an AMD Radeon RX 7700 XT;
- original and patched commits pinned by full SHA values.

The controls use the same type of sequential [architecture](glossary_EN.md#term-architecture) and the same software/hardware stack as the final matrix. They compare not only a terminal scalar metric but also intermediate states and parameter gradients. They therefore directly test the mechanism that affects training.

Stage 2 uses the following interpretation:

> Within the pinned experimental scope, `patched-v1` preserves the states and gradients computed by the original Torch2PC implementation within preregistered numerical tolerances. `patched-v1` can therefore serve as an implementation-behavior-preserving [candidate](glossary_EN.md#term-candidate) for measuring the effect of removing computational overhead.

## 8. Expected changes after patching

The following engineering quantities are expected to change:

- wall-clock training time;
- mean and median epoch time;
- the number of automatic-differentiation traversals;
- peak allocated and reserved GPU memory;
- [runtime](glossary_EN.md#term-runtime) ratios among BP, Exact, FixedPred, and Strict.

These changes are the target of Stage 2 and are not treated as a violation of mathematical equivalence.

Small differences in terminal training metrics between independent runs may arise from float32 [execution](glossary_EN.md#term-execution), GPU kernels, and accumulated rounding. Quality is therefore evaluated on the complete paired matrix rather than one cell.

## 9. Claim limitations

The [evidence](glossary_EN.md#term-evidence) does not automatically extend to:

- arbitrary models outside the tested sequential [execution](glossary_EN.md#term-execution) path;
- stochastic layers operated under different modes;
- custom automatic-differentiation functions with side effects;
- modules that depend on in-place mutation or storage aliasing;
- higher-order gradients;
- other PyTorch, ROCm, or CUDA versions;
- other Torch2PC commits;
- explicit-`vinit` modes beyond the dedicated regression test;
- hyperparameters and inference procedures absent from the control protocol.

Extending the scope requires repeating the structural and numerical controls in a newly pinned environment.

## 10. Reproducing the checks

### 10.1. Patch verification

```bash
sha256sum -c patches/torch2pc-patched-v1.patch.sha256

git -C external/Torch2PC diff --check \
  00c6c50ee3540537bbb56ab2b6567b541f42b093..\
b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
```

### 10.2. Candidate tests

```bash
.venv/bin/python -m pytest -q \
  external/Torch2PC/tests/test_patch_equivalence.py
```

### 10.3. Environment lock

```bash
sha256sum results/stage-2/summaries/environment-lock.json

jq '{
  source_git_commit_at_lock_creation,
  image_source_git_commit,
  torch2pc_commit,
  torch2pc_reference_commit,
  torch2pc_worktree_clean,
  torch2pc_reference_worktree_clean
}' results/stage-2/summaries/environment-lock.json
```

### 10.4. Numerical gates

```bash
jq '{
  device,
  thresholds,
  C0_exact_vs_bp,
  C1_fixedpred_vs_exact,
  C2_C3_original_vs_patched,
  gate_observed_within_thresholds
}' results/stage-2/summaries/control_gate_cpu.json

jq '{
  device,
  thresholds,
  C0_exact_vs_bp,
  C1_fixedpred_vs_exact,
  C2_C3_original_vs_patched,
  gate_observed_within_thresholds
}' results/stage-2/summaries/control_gate_gpu.json
```

### 10.5. Stage 2 protocol

```bash
PYTHONPATH=src .venv/bin/python3 \
  -m scripts.check_stage2_protocol_gate
```

Expected output:

```text
Protocol prerequisites observed for stage=final_stage_2
```

## 11. Related artifacts

- `patches/torch2pc-patched-v1.patch`
- `patches/torch2pc-patched-v1.patch.sha256`
- `docs/stage-2-protocol.md`
- `docs/stage-2-protocol_EN.md`
- `configs/stages/final_stage_2.yaml`
- `results/stage-2/summaries/prepared_assets.json`
- `results/stage-2/summaries/environment-lock.json`
- `results/stage-2/summaries/control_gate_cpu.json`
- `results/stage-2/summaries/control_gate_gpu.json`
- `results/stage-2/summaries/C0_exact_vs_bp_cpu.csv`
- `results/stage-2/summaries/C0_exact_vs_bp_gpu.csv`
- `results/stage-2/summaries/C1_fixedpred_vs_exact_cpu.csv`
- `results/stage-2/summaries/C1_fixedpred_vs_exact_gpu.csv`
- `results/stage-2/summaries/C2_C3_original_vs_patched_cpu.csv`
- `results/stage-2/summaries/C2_C3_original_vs_patched_gpu.csv`
- `results/stage-2/summaries/final_stage_2_execution_plan.json`
- `results/stage-2/summaries/stage-2-freeze_manifest.json`

## 12. Conclusion

The `torch2pc-patched-v1` patch corrects API defects and removes repeated forward and reverse traversals, repeated VJP-graph construction, and unnecessary tensor copies.

The core mathematical definitions of Exact, FixedPred, and Strict, the state-update order, differentiated functions, and parameter derivatives are preserved. The support consists of:

1. change analysis;
2. structural source checks;
3. candidate regression and equivalence tests;
4. CPU/float64 controls;
5. GPU/float32/ROCm controls;
6. complete pinning of commits, [configuration](glossary_EN.md#term-configuration), image, and environment.

Within final Stage 2, `patched-v1` is a justified replacement for the original implementation that preserves mathematical behavior and can be used to measure computational efficiency without changing the experimental mathematics.

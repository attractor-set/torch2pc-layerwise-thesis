# Reproducibility

[Русская версия](reproducibility.md)

## Pinned objects

| Object | Mechanism |
|---|---|
| Project code | Git commit |
| Torch2PC | full SHA and detached repository state |
| Container | tag, image ID, and base-image digest |
| Python | dependency lock files and `pip freeze` |
| Data | local manifest and SHA-256 |
| Splits | stored NPZ files and SHA-256 |
| Randomness | split, model, data-loader, and corruption seeds |
| [Execution](glossary_EN.md#term-execution) | dtype, device, workers, threads, and batch size |
| [Attempt](glossary_EN.md#term-attempt) | unique `run_id` |
| Results | authorized [configuration](glossary_EN.md#term-configuration), metrics, environment, and manifest |

## Determinism

`torch.use_deterministic_algorithms` is enabled in strict mode. When an
operation does not support determinism, the run must fail or use a separately
documented [configuration](glossary_EN.md#term-configuration). A warning without termination is insufficient for
the primary analysis.

## Repeatability and reproducibility

- repeatability: the same host, image, commit, and [configuration](glossary_EN.md#term-configuration);
- reproducibility: another compatible host with the same artifacts;
- statistical robustness: independently trained models with different
  `model_seed` values.

Bitwise floating-point agreement across different GPUs is not required;
prespecified tolerances and statistical conclusions are compared instead.

## Environment lock

`environment-lock.json` binds control and experimental runs to:

- SHA-256 digests of source and [configuration](glossary_EN.md#term-configuration) files;
- immutable Docker image IDs and `RepoDigest` values;
- the package inventory inside the container;
- the full Torch2PC commit;
- host, driver, and ROCm-tool information.

After a source or [configuration](glossary_EN.md#term-configuration) change, the lock is regenerated and C0/C1 are
repeated. Control results contain the lock-file SHA-256, so an artifact from a
different environment is not accepted automatically.

## Metric verifiability

Every completed [run](glossary_EN.md#term-run) stores validation predictions. [Final execution](glossary_EN.md#term-final-execution) also stores test
predictions with original example indices, true labels, predictions, and
probabilities. Aggregate metrics can therefore be recomputed without another
model run.

The public package includes code, configurations, references, aggregate
results, figures, and tables. It excludes publication PDFs, source datasets,
and large checkpoints.

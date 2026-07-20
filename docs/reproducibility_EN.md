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

## Canonical release assets and A1 CSV byte integrity

Large artifacts from completed Stage 2, Stage 3A, and Stage 3B B0 phases are
published as separate canonical assets in GitHub Releases. Their absence from
an automatically generated GitHub source archive does not mean that [evidence](glossary_EN.md#term-evidence)
is unavailable: each release asset is verified against its published SHA-256
and, where provided by the package, its internal inventory manifest.

The existence of those release assets does not resolve a separate historical
A1 CSV byte-reproducibility issue. The A1 v1 manifests were created for six CSV
types in each of the `cpu` and `rocm` lanes — twelve registered paths in total
— when records used `CRLF` terminators. Git subsequently normalized those text
files and checks them out, including through source archives, with `LF` line
endings. A direct `sha256sum -c` may therefore report mismatches for those
registered CSV files even though their tabular content has not changed.

The canonical compatibility check is implemented by
`verify_a1_evidence_manifest`. It accepts a mismatch only for the exact closed
set of twelve A1 CSV paths and only when a deterministic `LF`-to-`CRLF`
conversion reproduces the sealed digest. Every other artifact requires an
exact byte-for-byte match. Existing A1 manifests and digests are not rewritten
for the normalized `LF` bytes, because doing so would alter already sealed
evidence instead of documenting historical compatibility.

Two independent policies therefore apply:

- Stage 2, Stage 3A, and Stage 3B B0 release assets provide availability and
  integrity verification for the large artifacts of those phases;
- the registered `CRLF` → Git `LF` rule provides a bounded compatibility path
  for legacy A1 CSV files and does not extend to other files or new evidence
  packages.

## Metric verifiability

Every completed [run](glossary_EN.md#term-run) stores validation predictions. [Final execution](glossary_EN.md#term-final-execution) also stores test
predictions with original example indices, true labels, predictions, and
probabilities. Aggregate metrics can therefore be recomputed without another
model run.

The public package includes code, configurations, references, aggregate
results, figures, and tables. It excludes publication PDFs, source datasets,
and large checkpoints.

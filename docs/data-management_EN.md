# Data management plan

[Русская версия](data-management.md)

## Sources

The study uses public benchmark datasets downloaded through torchvision. The
repository stores instructions, metadata, and checksums rather than source
[dataset](glossary_EN.md#term-dataset) files.

## Splitting

Training and validation indices are created deterministically and stored
separately from test indices. The [pilot study](glossary_EN.md#term-pilot-study) does not construct a test-data
loader or produce a test-split artifact.

## Storage

- `data/` — local data excluded from Git;
- `results/splits/` — indices and checksums;
- `results/runs/` — local [attempt](glossary_EN.md#term-attempt) artifacts;
- `results/summaries/` — aggregate materials and compact verifiable pilot
  observations.

## Publication

The project publishes checksums, configurations, aggregate results, and
`pilot_observations.csv`, which permits recomputation of pilot-[configuration](glossary_EN.md#term-configuration)
selection without publishing checkpoints. Source [dataset](glossary_EN.md#term-dataset) files are not
redistributed unless licensing and the need for redistribution are reviewed
separately.

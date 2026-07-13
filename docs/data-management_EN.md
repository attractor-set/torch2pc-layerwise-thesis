# Data management plan

[Русская версия](data-management.md)

Datasets are downloaded locally through torchvision. The repository stores
instructions, metadata, deterministic split indices, and checksums rather than
redistributed dataset files. Pilot does not instantiate the test dataset.

Raw run directories and checkpoints remain local. The compact
`results/summaries/pilot_observations.csv` records one verified terminal row per
planned pilot cell, including validation metrics, timing, and cohort provenance.
This permits independent recomputation of pilot selection without publishing
model checkpoints or source dataset files.

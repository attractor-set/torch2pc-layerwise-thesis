# Data directory

[Русская версия](README.md)

The `data/` directory is reserved for local dataset assets and is excluded from
Git. The public dissertation release `v1.0.0` does not require downloading the
data again and does not authorize rerunning completed scientific protocols.

The historical preparation stage used `make prepare` and recorded:

- the list of files;
- file sizes;
- SHA-256 checksums;
- available dataset-version metadata;
- applied input transformations.

Registered scientific executions used datasets as pre-prepared local assets;
downloading or modifying datasets during the execution itself was not allowed.

A scientific experiment created after `v1.0.0` requires its own protocol, new
authorization, and a separate data-asset freeze. It is not a continuation or
rerun of a closed execution merely because it uses this directory.

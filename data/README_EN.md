# Data directory

[Русская версия](README.md)

Dataset files are downloaded locally with `make prepare` and are excluded
from Git.

The asset preparation stage records:

- the list of files;
- file sizes;
- SHA-256 checksums;
- dataset-related metadata available through the selected library;
- applied input transformations.

Final experiments must use the prepared local assets and must not download or
modify datasets during execution.

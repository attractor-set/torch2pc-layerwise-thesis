# Reproducibility

[Русская версия](reproducibility.md)

The project records source commits, container identity, locked dependencies, dataset and split checksums, seeds, runtime parameters, unique attempts, resolved configurations, environments, and artifact manifests. Deterministic algorithms run in strict mode.

`environment-lock.json` binds runs to source/configuration hashes, immutable
Docker image IDs, the container package list, the Torch2PC commit, and host
state. Controls are repeated after a lock-changing modification. Final runs
store per-sample predictions and original dataset indices.

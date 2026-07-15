# Run checklist

[Русская версия](run-checklist.md)

- [ ] The Git worktree has the expected status.
- [ ] The base image is available, and its image ID and `RepoDigest` are recorded.
- [ ] The image contains a label with the full source Git commit.
- [ ] `environment-lock.json` matches current code and [configuration](../glossary_EN.md#term-configuration) hashes.
- [ ] The Torch2PC commit is pinned.
- [ ] [Dataset](../glossary_EN.md#term-dataset) checksums are recorded.
- [ ] C0 CPU has passed.
- [ ] C1 CPU has passed.
- [ ] C0 GPU has passed.
- [ ] C1 GPU has passed.
- [ ] The [pilot study](../glossary_EN.md#term-pilot-study) contains no test metrics.
- [ ] The pilot [configuration](../glossary_EN.md#term-configuration) is frozen.
- [ ] The final configuration hash matches the freeze manifest.
- [ ] Failed runs are retained.
- [ ] Validation and test per-sample predictions retain original indices.
- [ ] Environment and artifact manifests are created.

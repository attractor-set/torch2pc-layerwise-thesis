# Run checklist

[Русская версия](run-checklist.md)

Verify image identity, pinned Torch2PC, dataset checksums, CPU/GPU controls, absence of pilot test metrics, pilot freeze, failed-run retention, and manifests.

- [ ] The image contains the full source Git revision label.
- [ ] `environment-lock.json` matches current code and configuration hashes.
- [ ] Per-sample predictions retain original dataset indices.

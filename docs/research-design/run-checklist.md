# Контрольный список запуска

[English version](run-checklist_EN.md)

- [ ] Git working tree имеет ожидаемый статус.
- [ ] Base image доступен, а image ID и RepoDigest записаны.
- [ ] Образ содержит label с полным source Git commit.
- [ ] `environment-lock.json` соответствует текущим code/config hashes.
- [ ] Torch2PC commit закреплен.
- [ ] Dataset checksums записаны.
- [ ] C0 CPU выполнен.
- [ ] C1 CPU выполнен.
- [ ] C0 GPU выполнен.
- [ ] C1 GPU выполнен.
- [ ] Pilot не содержит test metrics.
- [ ] Pilot configuration frozen.
- [ ] Final config hash совпадает с freeze manifest.
- [ ] Failed runs сохранены.
- [ ] Per-sample validation/test predictions сохранены с source indices.
- [ ] Environment и artifact manifests созданы.

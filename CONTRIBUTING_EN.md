# Contributing

[Русская версия](CONTRIBUTING.md)

Changes must preserve the distinction between validation-based selection and
final test evaluation. Do not modify a frozen final configuration after test
access without creating a new explicitly exploratory experiment.

Workflow:

1. Open an Issue.
2. Create a focused branch.
3. Add tests and update documentation.
4. Run `make lint typecheck test validate`.
5. Open a Pull Request.
6. Link result-changing work to an experiment or ADR.

Do not commit datasets, article PDFs, large checkpoints, or private comments.

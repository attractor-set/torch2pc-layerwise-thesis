# GitHub repository setup

[Русская версия](github-setup.md)

This document records the repository's **historical bootstrap procedure**. For
the existing public `v1.0.0` project it is not a current repository-creation
plan and must not be rerun as the release procedure.

The historical sequence was:

1. verify author metadata and the repository URL in `CITATION.cff`,
   `pyproject.toml`, and LaTeX;
2. run `./scripts/bootstrap_github.sh`;
3. create the empty remote repository;
4. push `main`;
5. enable Issues, Discussions, Projects, and branch protection;
6. require the `ci`, `docs`, and `thesis-build` checks;
7. create a GitHub Project for research-task management;
8. after the first public release, optionally connect the repository to an
   archival DOI service.

The current dissertation publication procedure is defined by the release
workflow, `scripts/build_release.sh`, `scripts/check_release_contract.py`, and
`docs/validation_EN.md`.

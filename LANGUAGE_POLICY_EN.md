# Project language policy

[Русская версия](LANGUAGE_POLICY.md)

## Primary language

Russian is the primary language of the repository, documentation, Issues,
Pull Requests, and dissertation.

## English versions

An English user-facing document receives the `_EN` suffix:

```text
README.md              -> README_EN.md
STATUS.md              -> STATUS_EN.md
docs/methodology.md    -> docs/methodology_EN.md
article/README.md      -> article/README_EN.md
```

## Exceptions

Standard technical names remain unchanged:

- Python modules, functions, classes, and configuration keys;
- `LICENSE`, because GitHub detects the conventional filename;
- `CITATION.cff`, because the format is standardized;
- `Dockerfile`, `Makefile`, `compose.yaml`, and `pyproject.toml`;
- GitHub Actions and YAML keys;
- BibTeX citation keys;
- the English article source `manuscript_EN.tex`.

## Update rules

1. Update the Russian version first.
2. Update the English version in the same Pull Request.
3. Record temporarily missing translations in an Issue.
4. `scripts/check_language_structure.py` verifies required document pairs.
5. Scientific data, numbers, and citations must match across languages.

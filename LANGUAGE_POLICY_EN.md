# Language and terminology policy

[Русская версия](LANGUAGE_POLICY.md)

## Primary language

Russian is the primary language of the repository, user-facing documentation,
discussions, pull requests, and dissertation. English versions are maintained
in parallel for international review and publication.

## Paired documents

An English user-facing document receives the `_EN` suffix:

```text
README.md              -> README_EN.md
STATUS.md              -> STATUS_EN.md
docs/methodology.md    -> docs/methodology_EN.md
article/README.md      -> article/README_EN.md
```

Russian and English versions must agree on facts, numerical values, links,
claim boundaries, and stage status. Syntax and word order may differ when the
meaning remains equivalent.

## Terminology principle

Russian prose uses the established Russian term first. On first substantive
use, the term links to its entry in the normative glossary. The English
equivalent is not duplicated in Russian running prose because the glossary
stores the language mapping. Direct English use is limited to quotations,
external-source titles, method names, and software identifiers. Method names,
fields, files, tags, branches, and commands remain unchanged and are formatted
as code.

English prose uses established machine-learning and software-engineering
terminology. Literal translations that are uncommon in scientific writing are
replaced with conventional English expressions.

## Normative glossary

Canonical definitions and Russian–English equivalents are maintained in the
[research glossary](docs/glossary_EN.md). The glossary is the sole normative
source for term meaning; this policy defines how terms are selected and
changed.

Every glossary entry has a stable `TERM-*` identifier shared by both language
versions. A term’s meaning, scope boundary, and usage rule are updated together
in `docs/glossary.md` and `docs/glossary_EN.md`.

Reserved terms for the next research line establish design vocabulary but do
not imply a completed experiment or an authorized empirical claim.

## Technical exceptions

The following retain their standard technical names:

- Python modules, functions, classes, and configuration fields;
- `LICENSE`, `CITATION.cff`, `Dockerfile`, `Makefile`, `compose.yaml`, and
  `pyproject.toml`;
- GitHub Actions, YAML, and JSON keys;
- BibTeX citation keys;
- Torch2PC method names, files, branches, tags, and GitHub Releases;
- established abbreviations including BP, CKA, RSA, VJP, CPU, GPU, ROCm,
  SHA-256, and PID.

## Update rules

1. Update the Russian version first.
2. Update the English version in the same pull request.
3. Use one term for one concept across all central documents.
4. Add a new term to both glossary versions before broad use.
5. Keep scientific data, numbers, links, and claim boundaries aligned.
6. `scripts/check_language_structure.py` verifies document pairs and language
   structure.
7. `scripts/check_glossary_usage.py` verifies first-use glossary links and the
   absence of noncanonical English prose in Russian documents.
8. Before publication, search README, STATUS, ROADMAP, CHANGELOG, protocol
   documents, and result reports for competing variants of each term.

## Source-code language

Program identifiers and APIs remain English for compatibility with Python,
Torch2PC, and the scientific software ecosystem. User-facing messages,
explanations, and documentation follow this policy.

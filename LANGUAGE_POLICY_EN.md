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
8. Before each public release, search README, STATUS, ROADMAP, CHANGELOG, protocol
   documents, and result reports for competing variants of each term.

## Source-code language

Program identifiers and APIs remain English for compatibility with Python,
Torch2PC, and the scientific software ecosystem. User-facing messages,
explanations, and documentation follow this policy.

## Bilingual equivalence contract

Paired documents must remain equivalent in facts, claim boundaries, stage
state, and stable identifiers, but equivalence is not defined by equality of
the set of digits that happen to occur in prose.

Automated validation separates three levels:

- the structural level checks pair registration, document language, heading
  hierarchy, and long immutable identifiers;
- the semantic level may declare language-neutral facts with hidden
  `LANG-FACT` comments whose values are valid JSON, or a shared
  machine-readable source with `LANG-SOURCE`;
- drift in undeclared numeric literals is emitted as a diagnostic warning and
  does not by itself make a translation invalid.

Fact form:

```text
<!-- LANG-FACT: measured_pair_count = 12 -->
<!-- LANG-FACT: cpu_affinity = [0] -->
```

Shared-source form:

```text
<!-- LANG-SOURCE: ../../experiments/frozen/example/contract.json -->
```

If `LANG-FACT` or `LANG-SOURCE` occurs in either member of a pair, the
corresponding contract must be identical in both versions. New or materially
changed documents with normative quantitative claims should prefer a
`LANG-SOURCE` that points to an existing machine-readable contract; Markdown
then remains a language representation rather than a second source of truth.

## Markdown language surface

Language validation applies to **human prose**, not to the aggregate of every
letter in the Markdown bytes. Machine-readable and verbatim surfaces must not
artificially dilute the Russian or English natural-language signal.

`scripts/check_language_structure.py` builds a `markdown_prose_surface` and
excludes fenced code blocks, inline code, HTML comments (including
`LANG-FACT`/`LANG-SOURCE`), URLs and link destinations, reference definitions,
long machine hashes, paths, CLI options, assignment-like machine markers, and
ALL_CAPS identifiers from the language ratio. Human-visible link labels remain
part of prose.

This separation does not weaken machine-surface validation: those surfaces are
covered by dedicated structural and semantic contracts, including heading
hierarchy, long-hash parity, `LANG-FACT`, `LANG-SOURCE`, and diagnostic numeric
literal drift. Per-file or per-ADR exemptions are forbidden.

The language threshold remains a blocking gate, but is computed on the prose
surface. A document made only of machine blocks has zero language signal and
cannot pass as Russian or English documentation without substantive prose.

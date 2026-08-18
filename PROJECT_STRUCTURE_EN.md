# Repository structure

[Русская версия](PROJECT_STRUCTURE.md)

The `v1.0.1` repository combines three surfaces that must remain distinct: the
**final dissertation**, the **executable research implementation**, and the
**historical experimental provenance**.

## Top-level map

```text
.
├── thesis/                  # final RU/EN dissertation and thesis-facing contracts
│   ├── main.tex             # Russian entrypoint
│   ├── main_EN.tex          # complete English entrypoint
│   ├── chapters/
│   ├── appendices/
│   ├── frontmatter/
│   ├── data/                # C01–C11, verified summaries, traceability
│   └── generated/           # locally rendered, not the source of truth
├── src/torch2pc_thesis/     # executable research logic and CLI
├── tests/                   # unit/correctness/integration regression surface
├── configs/                 # Stage 1/2/3 and hardware configuration
├── experiments/             # planned/frozen/completed lifecycle and authorization records
├── results/                 # aggregate results and compact evidence packages
├── docs/                    # theory, methodology, glossary, ADRs, protocols
├── references/              # BibTeX and source traceability
├── article/                 # secondary future-article package
├── notebooks/               # analysis-only and historical migration notebooks
├── scripts/                 # validation, provenance, thesis, and release tooling
├── requirements/            # CPU/ROCm/development dependency surfaces
├── external/                # locally bound external implementations
├── private/                 # excluded from the public scientific claim surface
└── .github/workflows/       # CI, thesis build, and tag-bound release
```

## Authoritative v1.0.1 surfaces

### `thesis/`

The final scientific narrative. Main machine-readable contracts are:

- `thesis/data/research_claims.json` — registered C01–C11 claims;
- `thesis/data/thesis_traceability.json` — theory → methodology → experiment →
  results → discussion → conclusion binding for every claim;
- `thesis/data/qwake_c2_verified_summary.json` — thesis-facing QWake C2
  aggregates with provenance bindings;
- `scripts/build_thesis_assets.py` — validation/rendering of Russian generated assets;
- `scripts/build_thesis_assets_en.py` — English generated assets from the same data contracts;
- `scripts/check_thesis_language_congruence.py` — RU/EN structural and scientific-semantic congruence;
- `scripts/check_thesis_semantic_contract.py` — terminology, statuses, and
  QWake action semantics;
- `scripts/check_thesis_traceability.py` — local claim-to-section binding.

`make thesis-check` validates the scientific and bilingual surface without LaTeX;
`make thesis` builds the Russian PDF, `make thesis-en` the English PDF, and
`make thesis-all` builds both renderings.

### `src/torch2pc_thesis/`

Canonical executable research implementation. Notebooks must not contain unique
scientific logic absent from `src/`.

### `experiments/` and `results/`

`experiments/` preserves protocol, freeze, authorization, and receipt lifecycle
artifacts. `results/` stores tracked aggregate outputs and compact evidence
packages. Historical execution-control documents retain the state of their own
time and are not current authorization for a new run.

### `docs/`

- `glossary.md` / `_EN` — normative terminology;
- `pc-tref-*` — task-relative theoretical framework;
- `pc-catm-*` — distinct mechanistic diagnostic level;
- `qwake-*` — architecture and historical bounded protocol surfaces;
- `decisions/` — ADRs, including immutable historical decisions;
- `research-log/` — point-in-time research history.

Read the current outcome from `README_EN.md`, `STATUS_EN.md`, and the final
thesis. Historical protocol/ADR statements are not rewritten after results are
known.

## Release surface

Tag `v1.0.1` is bound to an exact source commit/tree. `scripts/build_release.sh`
creates the source archive, separate `-ru.pdf`/`-en.pdf` artifacts, their SHA-256
files, metadata, and `release-manifest.json`. One manifest binds both language
renderings to the same source commit/tree. The GitHub workflow publishes those
exact assets and refuses to overwrite an existing release.

## Historical documents

`HYPOTHESES.md`, `PREREGISTRATION.md`, earlier Stage/QWake plans, ADRs,
`STATUS_EN.md`/`ROADMAP_EN.md` historical ledgers, and image IDs such as
`torch2pc-layerwise-thesis:0.1.0-...` are provenance. Their versions and local
open/closed states are not retroactively normalized to `v1.0.1`.

`pyproject.toml` and `src/torch2pc_thesis/__init__.py` belong to frozen QWake
scientific runtime closures and therefore retain the historical package version
`0.1.0` and their registered SHA-256 identities. Repository publication release
version authority is the separate `RELEASE_VERSION`, `CITATION.cff`, and the tag;
frozen runtime source must not be rewritten merely to synchronize release text.

## Post-v1.0.1 extension rule

New scientific work does not automatically continue an old claim identifier:

```text
new question
-> preregistered protocol / new claim identifier
-> immutable source + environment binding
-> authorized execution
-> preserved evidence
-> independent verification
-> bounded claim decision
-> optional dissertation/article successor
```

In particular, future C10 testing or a new confirmatory surface requires a new
protocol ID and does not redefine C09/C11 from the current dissertation.

# Repository structure

[Русская версия](PROJECT_STRUCTURE.md)

The `v1.0.0` repository combines three surfaces that must remain distinct: the
**final dissertation**, the **executable research implementation**, and the
**historical experimental provenance**.

## Top-level map

```text
.
├── thesis/                  # final dissertation and thesis-facing contracts
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

## Authoritative v1.0.0 surfaces

### `thesis/`

The final scientific narrative. Main machine-readable contracts are:

- `thesis/data/research_claims.json` — registered C01–C11 claims;
- `thesis/data/thesis_traceability.json` — theory → methodology → experiment →
  results → discussion → conclusion binding for every claim;
- `thesis/data/qwake_c2_verified_summary.json` — thesis-facing QWake C2
  aggregates with provenance bindings;
- `scripts/build_thesis_assets.py` — validation/rendering of generated assets;
- `scripts/check_thesis_semantic_contract.py` — terminology, statuses, and
  QWake action semantics;
- `scripts/check_thesis_traceability.py` — local claim-to-section binding.

`make thesis-check` validates the scientific surface without LaTeX; `make thesis`
builds the final PDF.

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

Tag `v1.0.0` is bound to an exact source commit/tree. `scripts/build_release.sh`
creates the source archive, PDF, SHA-256 files, metadata, and `release-manifest.json`.
The GitHub workflow publishes those exact assets and refuses to overwrite an
existing release.

## Historical documents

`HYPOTHESES.md`, `PREREGISTRATION.md`, earlier Stage/QWake plans, ADRs,
`STATUS_EN.md`/`ROADMAP_EN.md` historical ledgers, and image IDs such as
`torch2pc-layerwise-thesis:0.1.0-...` are provenance. Their versions and local
open/closed states are not retroactively normalized to `v1.0.0`.

## Post-v1.0.0 extension rule

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

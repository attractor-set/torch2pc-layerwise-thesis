# Final dissertation

[Русская версия](README.md)

`thesis/main.tex` is the Russian entrypoint for the completed dissertation;
`thesis/main_EN.tex` is the complete English rendering of the same scientific
work. The repository scaffold remains neutral with respect to a
department-specific title page. The scientific narrative, C01–C11, and final
evidence bindings are closed after T24; `v1.0.1` adds a language rendering, not
a new scientific result.

## Build

```bash
make thesis-check
make thesis       # Russian / RU
make thesis-en    # English / EN
make thesis-all   # both renderings
```

`make thesis-check` includes a dedicated structural and scientific-semantic
RU/EN congruence gate. The gate additionally requires matching structural
environments and normalized label sequences and checks chapter-level text-volume
ratios as an omission guard. Both PDFs consume the same canonical RU and EN
abstract bodies, differing only in their order. English tables and registries
are generated from the same `thesis/data/*.json` contracts as the Russian
rendering; translation must not change a claim ID, epistemic status, or inference
boundary.

The frozen T24 Russian rendering is 99 pages. The complete English rendering is
a separate document artifact and may have a different page count because of
language length and layout; equal pagination is not a semantic-equivalence
criterion.

## Machine-readable thesis contract

- `data/research_claims.json` — final C01–C11 and epistemic statuses;
- `data/thesis_traceability.json` — theory → methodology → experiment → result →
  discussion → conclusion binding;
- `data/qwake_c2_verified_summary.json` — independently reconciled thesis-facing
  C2 summary;
- `../scripts/build_thesis_assets.py` — Russian generated assets;
- `../scripts/build_thesis_assets_en.py` — English generated assets from the
  same scientific contracts;
- `../scripts/check_thesis_semantic_contract.py` — terminology and claim
  semantics, including QWake action semantics;
- `../scripts/check_thesis_traceability.py` — local claim binding;
- `../scripts/check_thesis_language_congruence.py` — RU/EN structure,
  terminology, critical numbers, and C08–C11 status boundaries.

Generated `.tex` assets are not an independent source of truth; they are built
from tracked data/contracts before each thesis build.

## v1.0.1 release

The release publishes two language-explicit PDFs:

```text
torch2pc-layerwise-thesis-1.0.1-ru.pdf
torch2pc-layerwise-thesis-1.0.1-en.pdf
```

Each PDF has its own SHA-256. One release manifest binds both artifacts to the
same source commit/tree.

## Final boundary

C08 remains `supported`, C09 is `rejected`, and C10/C11 are `not_tested`.
Translation, document building, and release operations do not open another
scientific execution or change those statuses.

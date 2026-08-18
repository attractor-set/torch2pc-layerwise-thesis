# Final dissertation

[Русская версия](README.md)

`thesis/main.tex` is the source entrypoint for the completed dissertation. The
repository scaffold remains neutral with respect to a department-specific title
page, while the scientific narrative, C01–C11, and final evidence bindings are
closed after T24.

## Build

```bash
make thesis-check
make thesis
```

T24 exact-commit assurance produced a 99-page build with no overfull boxes,
undefined references/citations, or pending cross-reference rerun warnings. The
`v1.0.0` release builder repeats the document gates on the exact release commit
and publishes the PDF with source/archive SHA-256 and commit/tree manifest.

## Machine-readable thesis contract

- `data/research_claims.json` — final C01–C11 and epistemic statuses;
- `data/thesis_traceability.json` — theory → methodology → experiment → result →
  discussion → conclusion binding;
- `data/qwake_c2_verified_summary.json` — independently reconciled thesis-facing
  C2 summary;
- `../scripts/build_thesis_assets.py` — provenance/numeric reconciliation;
- `../scripts/check_thesis_semantic_contract.py` — terminology and claim
  semantics, including QWake action semantics;
- `../scripts/check_thesis_traceability.py` — local claim binding.

Generated `.tex` assets are not an independent source of truth; they are built
from tracked data/contracts before each thesis build.

## Final boundary

C08 remains `supported`, C09 is `rejected`, and C10/C11 are `not_tested`.
No release/documentation operation opens another scientific execution or changes
those statuses.

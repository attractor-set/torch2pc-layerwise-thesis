# Thesis-facing data

This directory contains compact, Git-tracked inputs used to build the dissertation.
They are document inputs, not replacements for the underlying scientific evidence.

- `research_claims.json` is the dissertation claims contract: research questions,
  claim status, scope, and evidence locator.
- `qwake_c2_verified_summary.json` is a thesis-facing summary of the independently
  verified sealed QWake C2 Attempt-002 result. It records frozen source identities,
  aggregate values, protocol consequences, and arithmetic needed by the dissertation.
  The thesis build reconciles C08--C11 against those frozen aggregates and protocol
  facts without re-running policy evaluation or changing the cost model. It is
  explicitly marked `not_new_scientific_evidence`.

`python3 scripts/build_thesis_assets.py --check` validates the internal consistency
of these files without writing generated assets. `make thesis` renders the LaTeX
claims matrix from them before compiling the PDF.

`core_results_verified_summary.json` is a compact thesis-facing projection of
tracked Stage 1/2/3 evidence. Its `source_bindings` map pins every upstream
artifact by SHA-256. `scripts/build_thesis_assets.py` rehashes those files and
reconciles the selected aggregates against the upstream CSV/JSON content before
rendering dissertation tables. It is not a replacement for the underlying
evidence and is explicitly marked `not_new_scientific_evidence`.

## Reproducibility manifest

During `make thesis`, `scripts/build_thesis_assets.py` also renders
`thesis/generated/reproducibility_manifest.tex` from the validated source
bindings and frozen QWake identities. The generated table is documentation of
provenance, not new scientific evidence.

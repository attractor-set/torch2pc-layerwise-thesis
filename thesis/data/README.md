# Thesis-facing data

This directory contains compact, Git-tracked inputs used to build the dissertation.
They are document inputs, not replacements for the underlying scientific evidence.

- `research_claims.json` is the dissertation claims contract: research questions,
  claim status, scope, and evidence locator.
- `qwake_c2_verified_summary.json` is a thesis-facing summary of the independently
  verified sealed QWake C2 Attempt-002 result. It records frozen source identities,
  aggregate values, protocol consequences, and arithmetic needed by the dissertation.
  It is explicitly marked `not_new_scientific_evidence`.

`python3 scripts/build_thesis_assets.py --check` validates the internal consistency
of these files without writing generated assets. `make thesis` renders the LaTeX
claims matrix from them before compiling the PDF.

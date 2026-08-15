# Dissertation source

[Русская версия](README.md)


`main.tex` is a neutral LaTeX scaffold, not an official MEPhI template. It
contains neutral abstracts, an abbreviations section, the main chapters, and a
reproducibility appendix. Replace title-page and formatting elements with the
department-approved template before submission.

Generated tables and figures are referenced from `../results/`.
Do not manually copy numerical values into chapters when an automatically
generated table is available.

Build:

```bash
make thesis
```

The dissertation is built with XeLaTeX and Liberation system fonts.

## Dissertation contract and provenance

`make thesis` validates the machine-readable claims and thesis-facing result
summaries before rendering generated LaTeX assets. The generated
`reproducibility_manifest.tex` binds tracked Stage 1/2/3 evidence and frozen
QWake identities without copying the full forensic evidence surface into the
dissertation source tree.

Run the data/provenance gates without LaTeX with:

```bash
make thesis-check
```

# Torch2PC Layer-wise Thesis

[Русская версия](README.md)

![Python](https://img.shields.io/badge/Python-3.12-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.9.1-ee4c2c)
![ROCm](https://img.shields.io/badge/ROCm-7.2.1-ED1C24)
![Version](https://img.shields.io/badge/release-v1.0.0-blue)
![Code](https://img.shields.io/badge/code-Apache--2.0-green)
![Documents](https://img.shields.io/badge/docs-CC%20BY%204.0-green)

Research repository for the completed dissertation on layer-wise, mechanistic,
and compute-matched comparison of backpropagation (BP) with predictive-coding
(PC) regimes implemented in Torch2PC.

The work deliberately separates claims that cannot substitute for one another:

1. final-behavior similarity;
2. similarity of internal gradients and representations;
3. compute cost and localization of that cost;
4. task-relative admissibility of replacing the remaining canonical compute;
5. pre-action recognizability of that admissibility;
6. economic viability under full decision-cost accounting.

The final dissertation source is in [`thesis/`](thesis/). Normative terminology
is defined in the [glossary](docs/glossary_EN.md), the current outcome is in
[`STATUS_EN.md`](STATUS_EN.md), and the post-thesis research program is in
[`ROADMAP_EN.md`](ROADMAP_EN.md).

## v1.0.0 status

The scientific narrative was closed after the independent T24 post-refactor
review. The scientific closure point is:

```text
T24_COMMIT=9d45c897d35225fd541aa1b96aeed7fa7e945531
T24_TREE=44575ea3aced7c76633aa05f6ac22b89a20c615f
T24_MERGE=3cd892a62bce947886214fa887bde64748b5bf33
T24_POST_MERGE_TREE_IDENTITY=PASS
THESIS_STATUS=DEFENSE_READY_WITH_EXPLICIT_EXTERNAL_VALIDITY_BOUNDARIES
```

T24 exact-commit assurance completed with **1732 passed, 8 skipped**; the
thesis builds to **99 pages** with no overfull boxes, undefined
references/citations, or pending cross-reference rerun warnings. Those numbers
belong to the T24 closure point; the release manifest separately binds the
concrete `v1.0.0` tag to its source commit/tree and published-asset SHA-256s.

## Research questions and final statuses

Machine-readable claim traceability is stored in
[`thesis/data/thesis_traceability.json`](thesis/data/thesis_traceability.json).

| RQ | Scope | Outcome |
|---|---|---|
| RQ1 | When are PC regimes close to BP in behavior and internal dynamics? | C01–C02 `supported` |
| RQ2 | Where does compute cost arise, and do exact alternative organizations preserve required equivalence/resource admission? | C03–C06 `supported`; C07 `descriptive` |
| RQ3 | Can an admissible early action be recognized before normal completion and yield positive savings? | C08 `supported`; C09 `rejected`; C10–C11 `not_tested` |

The key epistemic boundary for RQ3 is that QWake-FP establishes informational
feasibility on the registered calibration surface but not economic viability
under the frozen full decision-cost accounting. Rejected C09 does **not**
redefine C10: the marginal execution cost of a minimal recognizer was not
measured in this work.

## Theoretical framework

- **PC-TREF** is a distinct task-relative equivalence/sufficiency framework;
- **PC-CATM** is a distinct linked mechanistic diagnostic level;
- **QWake-PC** is the general residual-compute control architecture;
- **QWake-FP** is the bounded FixedPred implementation tested in the thesis.

In QWake-FP, an early action does not mean “no computation remains.” The
registered `fixedpred_eta1_wavefront_completion_v1` candidate replaces the
remaining canonical iterative suffix with bounded analytic completion, while
`complete_suffix_stage2_baseline_v1` remains the exact reference/fallback path.

Positive C08 is driven by `compute_step >= 5`; on this surface it therefore
establishes a temporal fixed-prefix boundary, not input-dependent adaptivity or
superiority of PC-CATM features.

## Main empirical results

- Stage 1/2: the registered final-quality surface is preserved while execution
  cost changes across regimes;
- Stage 3A: FixedPred is observably closer to BP than Strict in gradient
  direction and representations, while early-layer gradient norm is reduced;
- Stage 3B B0: substantial cost is localized to `state_inference`;
- `SI-MA0`: `COST-MA0` fails and the negative result is retained;
- `SI-MA1`: observer-cost calibration passes; the signed residual is not
  interpreted as negative physical cost;
- B1/B2: exact candidates pass registered equivalence gates but receive
  `reject_or_revise` at the separate resource continuation screen;
- QWake C2: 264 of 2,625 scalar rules have non-zero coverage with zero observed
  dangerous accepts; the maximum registered full-surface coverage is 216/756
  (28.57%), comprising 108 preterminal step-5 records and 108 terminal-boundary
  step-6 records;
- C09: no rule combines zero observed dangerous accepts, non-zero coverage, and
  positive aggregate net saving under frozen full decision-cost accounting.

Zero observed dangerous accepts on a finite calibration surface does not
establish population-level safety.

## Build the dissertation

```bash
make thesis-check
make thesis
```

`make thesis-check` validates the claim schema, numeric summaries, provenance,
terminology contract, QWake action semantics, and local C01–C11 traceability.
`make thesis` then renders thesis-facing assets and builds the PDF with
XeLaTeX/Biber.

## Release

Version `1.0.0` is published as a tag-bound release. The release pipeline builds:

```text
torch2pc-layerwise-thesis-1.0.0.zip
torch2pc-layerwise-thesis-1.0.0.zip.sha256
torch2pc-layerwise-thesis-1.0.0.pdf
torch2pc-layerwise-thesis-1.0.0.pdf.sha256
torch2pc-layerwise-thesis-1.0.0.metadata.json
torch2pc-layerwise-thesis-1.0.0.release-manifest.json
```

The manifest records the source commit/tree, source/PDF SHA-256s, page count,
and release/thesis gate outcomes. The release contract is checked by
`scripts/check_release_contract.py`.

## Repository

| Directory | Role |
|---|---|
| `thesis/` | final dissertation text, claim registry, and generated thesis assets |
| `src/torch2pc_thesis/` | executable research logic and CLI |
| `experiments/` | historical preregistration/freeze/authorization contracts and lifecycle records |
| `results/` | tracked aggregate results and compact evidence packages |
| `docs/` | glossary, theory, methodology, ADRs, and historical protocols |
| `configs/` | Stage 1/2/3 configurations and hardware profiles |
| `references/` | BibTeX/source traceability without redistributed PDFs |
| `article/` | secondary future article package; not release-defining for thesis v1.0.0 |

See [`PROJECT_STRUCTURE_EN.md`](PROJECT_STRUCTURE_EN.md) for the complete map.

## Historical artifacts

`HYPOTHESES.md`, `PREREGISTRATION.md`, earlier Stage/QWake plans, ADRs,
authorization/receipt/freeze documents, and point-in-time blocks embedded in
`STATUS_EN.md`/`ROADMAP_EN.md` preserve the state of their own stage. Their old
`open=false`, `execution closed`, or image-version statements must not be read
as the current v1.0.0 status. The authoritative current status is the top
section of `STATUS_EN.md`; final scientific statuses come from the dissertation
claim registry.

Historical image IDs such as `torch2pc-layerwise-thesis:0.1.0-...` are likewise
left unchanged because they are part of frozen provenance.

## Historical publication-contract compatibility

The markers below are retained in the README as historical regression anchors
for the previously published matched-profiling layer. They are **not** the
current QWake state and do not authorize new scientific execution:

```text
matched_profiling_analysis_publication_action_complete=true
matched_profiling_analysis_publication_receipt_frozen=true
results_publication_permitted=true
release_draft_required=false
release_publication_permitted=true
release_publication_complete=true
```

## Licensing

- code: Apache License 2.0 — [`LICENSE`](LICENSE);
- dissertation and documentation: CC BY 4.0 — [`LICENSE-DOCS_EN`](LICENSE-DOCS_EN);
- third-party materials: original rights and attribution terms — [`NOTICE_EN`](NOTICE_EN).

# Torch2PC Layer-wise Thesis

[Русская версия](README.md)

A master's thesis repository comparing backpropagation (BP) with predictive
coding regimes in Torch2PC. The project separates assumptions from
observations, procedures from results, and results from interpretation.

## Research stance

The project follows a neutral research stance:

- no method is assumed superior in advance;
- theoretical expectations are treated as testable assumptions;
- failure to detect a difference is not treated as equivalence without a
  dedicated equivalence analysis;
- empirical claims are accepted only within a preregistered experiment and a
  recorded compute environment;
- negative, mixed, and unstable outcomes are retained;
- conclusions remain limited to the studied implementation, architectures,
  datasets, and compute environment.

See [RESEARCH_PRINCIPLES_EN.md](RESEARCH_PRINCIPLES_EN.md).

## Research question

Under which algorithmic and computational conditions do `Exact`, `FixedPred`,
and `Strict` produce behavior close to BP, and when do their differences exceed
preregistered numerical or statistical bounds?

The comparison covers:

- implementation correctness and numerical controls;
- classification quality;
- layer-wise gradients;
- neural representations;
- robustness to corruption;
- compute time and memory;
- reproducibility across independent runs.

## Current state as of 15 July 2026

The following are complete in the pinned Ubuntu/ROCm environment:

- validation-only pilot: **96/96**, without test-dataset access;
- Stage 1: **80/80** with original Torch2PC
  `00c6c50ee3540537bbb56ab2b6567b541f42b093`;
- Stage 2: **80/80** with patched Torch2PC
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- Stage 3A: layer-wise diagnostics, model-seed statistics, depth analysis, and
  publication figures;
- Stage 3B B0: ROCm/float32 canonical baseline, 96/96 cells, with no failed
  attempts or systemic resource failures;
- Stage 3B B0: statistical and engineering analysis published without
  rerunning the baseline campaign.

Stage 3A and Stage 3B B0 did not access the test dataset. CI is the source of
truth for current regression checks; the documentation does not pin a quickly
stale test count.

See [STATUS_EN.md](STATUS_EN.md) for details and
[ROADMAP_EN.md](ROADMAP_EN.md) for the remaining sequence.

## Main published results

### Stage 1 and Stage 2

The Stage 2 intervention preserved the experimental protocol and changed only
the compute path. Relative to Stage 1 mean total training time:

- Exact was approximately 14% faster;
- FixedPred was approximately 31% faster;
- Strict was approximately 26% faster;
- BP was effectively unchanged.

Observed Stage 2 runtime ordering:
`BP ≈ Exact < FixedPred << Strict`.

Paired records are published under
[`results/cross-version/`](results/cross-version/).

### Stage 3A

The confirmatory campaign covers FashionMNIST, `lenet_classic`, and seeds 0–9.
Published outputs include:

- 2250 gradient observations;
- 150 representation CKA/RSA observations;
- 750 cross-layer CKA observations;
- 40 confirmatory gradient comparisons;
- 20 confirmatory representation comparisons;
- 24 statistical depth-analysis rows;
- 8 PDF figures.

Within the registered scope, `FixedPred` nearly preserves gradient direction
while strongly attenuating the norm in early layers. `Strict` differs from BP
in both direction and scale in hidden layers. `FixedPred` representations are
closer to BP than `Strict` representations.

Detailed report:
[docs/stage3a-statistical-results_EN.md](docs/stage3a-statistical-results_EN.md).

### Stage 3B B0

B0 fixes `stage2_baseline` for `FixedPred` and `Strict` in a synthetic
ROCm/float32 scaling campaign. The canonical protocol uses 20 warm-up steps,
5 repetitions, and 50 measured steps.

Completed outputs include:

- 96/96 canonical cells and 96/96 attempts;
- 0 failed attempts and 0 systemic resource failures;
- 96 process records and 96 unique child PIDs;
- 48 `FixedPred` and 48 `Strict` cells;
- 96 cell, 480 region, 48 paired, and 32 configuration rows;
- measured regions `initial_forward`, `state_inference`, `local_state_vjp`,
  `parameter_vjp`, and `optimizer_step`;
- non-perturbation, completeness, and finite-value checks.

Sealed evidence:
[`results/stage-3/profiling/b0/sealed-v1/`](results/stage-3/profiling/b0/sealed-v1/).
Bundle digest:
`6a3d61838810e559a39f13e6ac39d6b22624c21d72523bddb55c33e83063c93e`.

Engineering analysis:
[`results/stage-3/profiling/b0/analysis-v1/`](results/stage-3/profiling/b0/analysis-v1/).
The independently trained model identified by `model_seed` is the statistical
unit; three models are available per configuration.

Main bounded findings:

- median Strict/FixedPred device-time ratio: **2.327×**;
- median peak-allocated-memory ratio: **1.328×**;
- dominant device-time region: state inference (`state_inference`);
- Strict/FixedPred saved-tensor ratio within `state_inference`: **11.998×**.

These results are descriptive engineering analysis of the pinned matrix, not a
universal method ranking. The full Stage 3B program remains incomplete:
`full_stage3b_campaign_complete=false`.

## Execution and publication chain

| Role | Identifier |
|---|---|
| Stage 1 source state | `140e77cc2083bf04234dcea16b95803e63cb0537` |
| Stage 2 execution source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Stage 2 publication state | `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| Stage 3A publication tag | `stage3a-statistical-publication-v1` |
| Stage 3B B0 execution source | `95c25d35224abd5e741f1df9327662ff2fde23ad` |
| Stage 3B B0 integrity-sealing source | `caa226cc1cd5d4aa0f9772c1fb997f7388d60730` |
| Stage 3B B0 publication state | `ed0d48063a17e2d9c6679869a4d930f933877052` |
| Stage 3B B0 evidence tag | `stage3b-b0-evidence-v1` |
| Stage 3B B0 analysis implementation | `e7a1632a947fae578e877826f0c923342669430e` |
| Stage 3B B0 analysis publication state | `b9ff8b2ab76f8752b15dd3bb968565d05f1fe9d3` |
| Stage 3B B0 analysis tag | `stage3b-b0-analysis-evidence-v1` |

GitHub Releases:

- [`stage2-results-v1`](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage2-results-v1)
- [`stage3b-b0-evidence-v1`](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage3b-b0-evidence-v1)
- [`stage3b-b0-analysis-evidence-v1`](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage3b-b0-analysis-evidence-v1)

## Next stage

The next stage is candidate-specific numerical-equivalence testing for B1 and
B2. Each candidate must separately pass registered cosine, relative-L2,
finite-value, and stability criteria. A small profiling pilot is permitted only
after these checks pass. The full matched profiling matrix requires a separate
decision gate.

Structural-locality claims require dedicated measurements of dependency radius,
graph span and lifetime, the feedback operator, and orchestration barriers.

## Numerical controls

C0 and C1 are used instead of H0/H1 to avoid confusion with null statistical
hypotheses.

- **C0:** numerical comparison of `Exact` and BP gradients;
- **C1:** numerical comparison of `FixedPred` at `eta=1`, `n>=depth`, and
  `Exact`;
- **structural check:** inspection of selected Torch2PC expressions associated
  with the Rosenbaum 2025 correction.

Passing C0/C1 applies only to the pinned code, dtype, device, and test packages.
It is not a universal proof of algorithmic equivalence.

## Reproduction

Base environment preparation:

```bash
cp .env.example .env
./scripts/setup_ubuntu.sh
make init
make host-check
make image-check
make pin-base-image
make build
make validate
make prepare
```

`make pin-base-image` replaces a mutable Docker tag with an immutable
`repository@sha256:...` reference. The local `.env` is not committed.

See [docs/reproducibility_EN.md](docs/reproducibility_EN.md) and
[docs/validation_EN.md](docs/validation_EN.md) for the complete procedure.

## Test-dataset protection

- `smoke` and `pilot` do not create a test loader;
- test access is permitted only for `final`;
- `final` requires a frozen protocol and `pilot-freeze` artifact;
- each run records the resolved configuration, environment manifest, split
  checksums, per-sample predictions, metrics, and a unique `run_id`;
- a repeated successful run with the same code, configuration, and seed is
  blocked so repeated test inspection cannot count as a new replication.

## Repository structure

| Directory | Purpose |
|---|---|
| `src/torch2pc_thesis/` | Executable research logic and CLI |
| `configs/` | Base, hardware, stage, and method configurations |
| `experiments/` | Append-only run registry and experiment plans |
| `results/` | Aggregate public artifacts |
| `notebooks/analysis/` | Analysis of registered results |
| `notebooks/legacy/` | Historical migration-check notebook |
| `thesis/` | Russian dissertation scaffold |
| `article/` | English article scaffold with `_EN` suffix |
| `references/` | BibTeX and literature matrix without PDFs |
| `docs/` | Protocols, decisions, and research log |

See [PROJECT_STRUCTURE_EN.md](PROJECT_STRUCTURE_EN.md).

## Language and terminology

Russian is the primary language of user-facing materials. English versions use
the `_EN` suffix. Python, YAML, Torch2PC, and GitHub identifiers remain English.
Canonical terminology is defined in
[LANGUAGE_POLICY_EN.md](LANGUAGE_POLICY_EN.md).

## Licensing

- software code: Apache License 2.0 — [LICENSE](LICENSE);
- thesis, article, documentation, tables, and figures: Creative Commons
  Attribution 4.0 International — [LICENSE-DOCS](LICENSE-DOCS) and
  [LICENSE-DOCS_EN](LICENSE-DOCS_EN);
- third-party materials retain their original licenses and attribution terms —
  [NOTICE](NOTICE) and [NOTICE_EN](NOTICE_EN).

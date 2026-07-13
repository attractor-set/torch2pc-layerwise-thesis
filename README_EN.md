# Torch2PC Layer-wise Thesis

[Русская версия](README.md)

A master's thesis research repository for comparing backpropagation and
Torch2PC predictive-coding regimes. The repository separates assumptions,
observations, procedures, and interpretations.

## Research stance

The project adopts a neutral observer position:

- no method is assumed to be superior in advance;
- theoretical expectations are treated as testable assumptions;
- failure to detect a difference is not treated as equivalence without a
  dedicated equivalence analysis;
- empirical statements are accepted only within a pre-specified experiment and
  a recorded environment;
- negative, mixed, and unstable outcomes are retained;
- conclusions remain limited to the studied implementation, architectures,
  datasets, and compute environment.

## Research question

Under which algorithmic and computational conditions do `Exact`, `FixedPred`,
and `Strict` produce observations close to backpropagation, and when do the
observed differences exceed pre-specified numerical or statistical bounds?

## Observed status on 13 July 2026

The validation pilot and both confirmatory campaigns are complete in the pinned
Ubuntu/ROCm environment:

- validation-only pilot: **96/96** terminal cells, 0 failed, no test evaluation;
- Stage 1: **80/80**, original Torch2PC
  `00c6c50ee3540537bbb56ab2b6567b541f42b093`;
- Stage 2: **80/80**, patched Torch2PC
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- the scoped CPU/GPU numerical equivalence gates passed;
- the maintained regression suite contains **63 passing tests**;
- paired Stage 1/2 test accuracy and macro-F1 values matched for every dataset,
  method, and seed;
- the observed Stage 2 runtime ordering is
  `BP ≈ Exact < FixedPred << Strict`.

Relative to Stage 1 mean total training time, Exact was approximately 14%
faster, FixedPred 31% faster, and Strict 26% faster; BP was effectively
unchanged. Complete paired records are available in
[`results/cross-version/`](results/cross-version/).

### Execution and publication states

| Role | Identifier |
|---|---|
| Stage 1 source lock | `140e77cc2083bf04234dcea16b95803e63cb0537` |
| Stage 2 execution source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Stage 2 results/publication state | `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| Stage 1 tag | `confirmatory-final-v1` |
| Stage 2 execution tag | `stage2-execution-v1` |
| Stage 2 results tag | `stage2-results-v1` |

The
[`stage2-results-v1` GitHub Release](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage2-results-v1)
contains the replication archive, its SHA-256, and the file manifest; 660
manifest artifacts were verified. The execution tag identifies the code used
for the campaign, while the results tag identifies the later publication
state.

Stage 1 and Stage 2 are complete and are not intended to be rerun. Any new
performance-changing work belongs to a separately specified Stage 3 with its
own provenance chain.

See [RESEARCH_PRINCIPLES_EN.md](RESEARCH_PRINCIPLES_EN.md) and
[STATUS_EN.md](STATUS_EN.md).

## Stage 3: design-ready

The extended Stage 3 studies mathematical and execution locality, exact VJP
organization, adaptive stopping, periodic VJP refresh, and depth/width scaling.
See [docs/stage-3-protocol_EN.md](docs/stage-3-protocol_EN.md). Design revision 2 adds an exact-shortcut control and a separate predict-correct line with mandatory exact correction sweeps and Strict fallback.

The repository is ready for implementation of the profiling infrastructure,
while the profiling campaign, pilot, and final execution remain deliberately
blocked:

```bash
make stage3-ready
make stage3-plan
```

The deterministic design plan contains 336 short profiling cells, 48
parameterized core validation-only pilot cells, and 27 predict-correct
accelerator screening cells. Stage 3 is absent from `TRAINING_STAGES`, and the
final template keeps `evaluation.use_test=false` until a separate freeze.

## Pilot evidence export

`make pilot` generates both `pilot_selection.json` and the compact, verified
`pilot_observations.csv`. The latter can be regenerated while the original run
directories and pilot environment lock are still available:

```bash
make select-pilot
make pilot-observations
```

## Reproduction from scratch

The following sequence is for independent reproduction, not for repeating the
completed Stage 1/2 campaigns.

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

`make pin-base-image` replaces the mutable Docker tag in the local `.env` with
an immutable `repository@sha256:...` reference. Pilot and final images are built
only after this step. The local `.env` is not committed.

See [docs/validation_EN.md](docs/validation_EN.md) for the validation procedure.


## Public and local artifacts

Downloaded papers, datasets, private notes, and heavyweight checkpoints are not
stored in Git. Code, protocols, configurations, aggregate results, and
manifests are versioned. The complete Stage 2 raw artifacts are distributed in
the `stage2-results-v1` replication bundle.

## Licensing

- software code is distributed under the Apache License 2.0 — see
  [LICENSE](LICENSE);
- original thesis, article, documentation, table, and figure content is
  distributed under the Creative Commons Attribution 4.0 International license
  — see [LICENSE-DOCS](LICENSE-DOCS) and
  [LICENSE-DOCS_EN](LICENSE-DOCS_EN);
- third-party materials retain their original licenses and attribution terms —
  see [NOTICE](NOTICE) and [NOTICE_EN](NOTICE_EN).

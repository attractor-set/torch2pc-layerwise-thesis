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

The pinned Ubuntu/ROCm environment has completed the implementation controls
and the validation-only pilot:

- Torch2PC is pinned to
  `00c6c50ee3540537bbb56ab2b6567b541f42b093`;
- the target ROCm path was exercised on an AMD Radeon RX 7700 XT;
- C0 Exact/BP and C1 FixedPred/Exact satisfied their pre-specified CPU and GPU
  thresholds;
- all 96 pilot configuration-seed cells completed, with no failed cells;
- the pilot did not evaluate the test set;
- selected parameters are FixedPred `eta=0.1`, `n=10` and Strict `eta=0.05`,
  `n=20`;
- final remains blocked until the selected environment is re-locked, the short
  controls are repeated, and `pilot-freeze` is created.

These observations are implementation- and environment-scoped. They are not a
confirmatory comparison of method performance.

See [RESEARCH_PRINCIPLES_EN.md](RESEARCH_PRINCIPLES_EN.md) and
[STATUS_EN.md](STATUS_EN.md).


## Pilot evidence export

`make pilot` generates both `pilot_selection.json` and the compact, verified
`pilot_observations.csv`. The latter can be regenerated while the original run
directories and pilot environment lock are still available:

```bash
make select-pilot
make pilot-observations
```

## Controlled environment sequence

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

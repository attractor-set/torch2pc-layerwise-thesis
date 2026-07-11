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

## First-commit status

The first commit contains the repository structure, protocol, configuration
system, tests, controlled Ubuntu/ROCm environment, and executable experiment
scaffold. It contains no empirical result claims.

C0 and C1 are implementation controls, not statistical null hypotheses:

- C0 compares `Exact` and BP gradients;
- C1 compares `FixedPred` at `eta=1`, `n>=depth` with `Exact`.

Test data are unavailable to smoke and pilot stages. Final test evaluation is
allowed only after the pilot configuration is frozen.

See [RESEARCH_PRINCIPLES_EN.md](RESEARCH_PRINCIPLES_EN.md) and
[STATUS_EN.md](STATUS_EN.md).

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

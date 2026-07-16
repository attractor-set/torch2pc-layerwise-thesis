# Methodology

[Русская версия](methodology.md)

## Design

The study is a protocol-first comparison of BP and predictive-coding variants
in Torch2PC. Plans, [execution](glossary_EN.md#term-execution), [evidence](glossary_EN.md#term-evidence), analysis, and admission decisions are
separated by commits and tags. Negative and mixed results are retained without
changing frozen criteria.

## Completed stages

1. pilot and infrastructure validation;
2. Stage 1 — original Torch2PC;
3. Stage 2 — patched Torch2PC with verified equivalence;
4. Stage 3A — layer-wise gradients and representations;
5. Stage 3B B0 — canonical ROCm/float32 [profiling](glossary_EN.md#term-profiling);
6. `SI-MA0` — [mechanism attribution](glossary_EN.md#term-mechanism-attribution) with its negative cost gate retained;
7. `SI-MA1` — matched A/B/C observer calibration and final pass;
8. the `PC-TREF`/`PC-CATM` theoretical freeze before B1/B2.

## Data and independent unit

MNIST and FashionMNIST are used within their registered stages. The independent
statistical unit is the independently trained model identified by `model_seed`.
Batches, layers, steps, images, and timing blocks are nested observations, not
additional independent models.

The validation split supports selection, calibration, and [confirmatory analysis](glossary_EN.md#term-confirmatory-analysis)
under frozen contracts. The test split remains closed until the implementation,
features, thresholds, and statistical plan are frozen.

## Controlled environment

GPU/ROCm execution uses the canonical Docker image. The host is limited to
static, Git, and documentation checks. Each publication campaign freezes source
commit, image revision, Torch2PC revision, [configuration](glossary_EN.md#term-configuration), [checkpoint](glossary_EN.md#term-checkpoint) hashes,
and `SHA256SUMS`.

## Measurements

- quality and convergence;
- gradient geometry and depth effects;
- CKA, RSA, and cross-layer representation metrics;
- [device time](glossary_EN.md#term-device-time), wall time, memory, and [saved tensors](glossary_EN.md#term-saved-tensors);
- canonical correction channels, `NCZ`, `ECZ`, `TNZ`, and transport;
- [candidate](glossary_EN.md#term-candidate)/reference numerical equivalence;
- safety outcomes and [decision regret](glossary_EN.md#term-decision-regret);
- the [cost vector](glossary_EN.md#term-cost-vector).

Every `PC-CATM` norm has a measurement contract covering space, norm, scale,
dtype, device, epsilon, threshold, layer/step, and aggregation. Threshold
proximity is not called a quotient without an explicit partition map.

## Cost separation

The project accounts separately for:

1. [diagnostic-mechanism cost](glossary_EN.md#term-diagnostic-mechanism-cost);
2. [observer cost](glossary_EN.md#term-observer-cost);
3. [control-plane cost](glossary_EN.md#term-control-plane-cost);
4. [fallback](glossary_EN.md#term-fallback) and end-to-end cost.

`SI-MA1` addresses the observer boundary. Its negative calibrated residual is
over-closure, not negative physical cost or future savings.

## B1/B2 method

Each candidate receives a separate preregistration before implementation. The
contract freezes reference path, state/belief/RNG restoration, scope, numerical
endpoints and tolerances, independent unit, replacement policy, safety/regret,
cost vector, observer/control separation, fallback, and stop rules.

Sequence:

1. deterministic and unit controls;
2. CPU structural check;
3. controlled ROCm smoke;
4. candidate-specific numerical-equivalence gate;
5. separate admission decision for confirmatory profiling;
6. matched confirmatory execution;
7. aggregation by `model_seed` without post-hoc exclusions.

## Statistics

Primary estimands, test direction, bootstrap seed, replication count,
multiplicity policy, and thresholds are frozen before confirmatory execution.
Nested measurements are reduced to `model_seed`. Descriptive analyses are not
retrospectively relabeled as confirmatory evidence.

## Limitations

Claims are bounded to registered datasets, `lenet_classic`, the Torch2PC
revision, checkpoints, float32/ROCm environment, and diagnostic family. B1/B2,
active `QWake-PC`, and transfer require their own evidence packages.

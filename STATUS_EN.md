# Research status

[Русская версия](STATUS.md)

As of 16 July 2026, immutable Stage 1/2, Stage 3A, Stage 3B B0, `SI-MA0`, and
`SI-MA1` results are published. Full Stage 3B remains incomplete: B1/B2,
`EX-IF0`, passive diagnostics, the predictor, counterfactual exact verification,
and `QWake-PC` have not been executed.

## Status summary

| Component | Confirmed state |
|---|---|
| Pilot | 96/96; no test-split access |
| Stage 1 / Stage 2 | 80/80 and 80/80 |
| Stage 3A | layer-wise confirmatory evidence and publication complete |
| Stage 3B B0 | 96/96 ROCm/float32 cells; evidence and analysis published |
| `SI-MA0` | `REC/OBS/VER/CMP=true`, `COST=false`, global failure retained |
| `SI-MA1` execution | 10 model seeds, 3 batches/seed, 180 matched blocks |
| `SI-MA1` decision | `CAL-COST-MA1=true`, `si_ma1_passed=true` |
| B1/B2 theoretical prerequisite | satisfied by this `PC-TREF`/`PC-CATM` package |
| B1/B2 preregistration | permitted after package publication |
| B1/B2 implementation/execution | closed until candidate-specific contracts |
| Test split | closed |
| Full Stage 3B | `full_stage3b_campaign_complete=false` |

## Published results and boundaries

### Stage 3A

Within FashionMNIST, `lenet_classic`, and `model_seed=0..9`, `FixedPred`
largely preserves gradient direction while reducing early-layer norm, `Strict`
differs from BP in hidden-layer direction and scale, and `FixedPred`
representations are closer to BP than `Strict` representations. Layers,
batches, and images are not independent model replications.

### Stage 3B B0

B0 froze `stage2_baseline` for `FixedPred` and `Strict` in the synthetic
ROCm/float32 matrix. In the registered scope, the median Strict/FixedPred device
time ratio is `2.327×`, the peak allocated memory ratio is `1.328×`,
`state_inference` is the dominant time region, and the saved-tensor ratio in
that region is `11.998×`. This is bounded descriptive engineering analysis.

### `SI-MA0`

Across ten independently trained models, reconstruction, observer
non-interference, version coherence, and comparison gates passed, while
`COST-MA0` failed. The median accounting residual was approximately
`0.1606077466` against the registered `0.05` threshold. The global failure is
retained and is not rewritten by `SI-MA1`.

### `SI-MA1`

The matched A/B/C observer-calibration cohort contains 10 model seeds, 180
matched blocks, 27,000 arm-timing rows, 63,000 live-region rows, 360 numerical
comparisons, and 180 topology comparisons. The observed median
`D_seed=-0.190635073373`; the one-sided 95% bootstrap upper bound is
`-0.188621876160` against threshold `0.01`. `CAL-COST-MA1` and global `SI-MA1`
passed.

Signed values are retained. Negative residual is observer-calibration
over-closure, not negative physical cost. `SI-MA1` excludes future `ECZ`
evaluation, action selection, fallback validation, and end-to-end B1/B2
savings.

## Theoretical state

[PC-TREF Balanced Core](docs/pc-tref-balanced-core_EN.md),
[PC-CATM](docs/pc-catm-operator-model_EN.md), the
[theoretical foundation](docs/pc-tref-pc-catm-theoretical-foundation_EN.md), and
[ADR-013](docs/decisions/ADR-013-pc-tref-operational-semantics_EN.md) freeze a
partition-based diagnostic quotient, separate nontransitive threshold
proximity, regret-based required equivalence, operational task-relative defect,
precision-masked zero, explicit norm contracts, a cost vector, a preregistered
scalarization/Pareto rule, and separate diagnostic-mechanism, observer, and
control-plane costs.

This satisfies the B1/B2 theoretical prerequisite but does not establish
candidate speedup or safety.

## Provenance

| Artifact | Identifier |
|---|---|
| B0 evidence | `stage3b-b0-evidence-v1` |
| B0 analysis | `stage3b-b0-analysis-evidence-v1` |
| `SI-MA1` preregistration | `stage3b-si-ma1-prereg-v1` |
| `SI-MA1` implementation | `stage3b-si-ma1-implementation-v1` |
| `SI-MA1` execution | `stage3b-si-ma1-confirmatory-execution-v1` |
| `SI-MA1` final | `stage3b-si-ma1-confirmatory-v1` |
| `SI-MA1` publication commit | `9bf500a2494267e83cbf9657ad2f075e349a8a75` |

Raw and confirmatory outputs remain under
`results/stage-3/si-ma1/working/confirmatory/` and
`results/stage-3/si-ma1/confirmatory/`; documentation updates do not recreate
them.

## Next stage

The next permitted step is candidate-specific B1/B2 preregistration. Before
implementation, each contract defines the reference path, state/RNG
restoration, numerical-equivalence endpoints, regret and safety margins, norm
contracts, the cost vector, observer/control separation, fallback, and stop
rules. Full matched profiling, `EX-IF0`, active control, and test-split access
remain closed until their own decision gates.

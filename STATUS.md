# Статус исследования

[English version](STATUS_EN.md)

На 16 июля 2026 года опубликованы неизменяемые результаты Stage 1/2, Stage 3A,
Stage 3B B0, `SI-MA0` и `SI-MA1`. Полный Stage 3B остаётся незавершённым:
B1/B2, `EX-IF0`, passive diagnostics, predictor, counterfactual exact
verification и `QWake-PC` ещё не выполнены.

## Сводка состояния

| Компонент | Подтверждённое состояние |
|---|---|
| Pilot | 96/96; test split не использовался |
| Stage 1 / Stage 2 | 80/80 и 80/80 |
| Stage 3A | layer-wise confirmatory evidence и publication complete |
| Stage 3B B0 | 96/96 ROCm/float32 cells; evidence и analysis published |
| `SI-MA0` | `REC/OBS/VER/CMP=true`, `COST=false`, global fail retained |
| `SI-MA1` execution | 10 model seeds, 3 batches/seed, 180 matched blocks |
| `SI-MA1` decision | `CAL-COST-MA1=true`, `si_ma1_passed=true` |
| Теоретический prerequisite B1/B2 | выполнен `PC-TREF`/`PC-CATM` package |
| Предварительная регистрация B1/B2 | заморожена отдельными contracts; ожидает publication tag |
| Реализация B1 | открывается после preregistration tag |
| Реализация B2 | закрыта до sealed `EQ-B1` |
| Shared profiling B1/B2 | закрыто до sealed `EQ-B1` и `EQ-B2` |
| Test split | закрыт |
| Полный Stage 3B | `full_stage3b_campaign_complete=false` |

## Опубликованные результаты и границы

### Stage 3A

В области FashionMNIST, `lenet_classic` и `model_seed=0..9`:

- `FixedPred` почти сохраняет направление градиента, но уменьшает его норму в
  ранних слоях;
- `Strict` в скрытых слоях отличается от BP по направлению и масштабу;
- представления `FixedPred` ближе к BP, чем представления `Strict`;
- отдельные слои, batches и изображения не считаются независимыми моделями.

Результаты ограничены зарегистрированными checkpoints, реализацией и средой.

### Stage 3B B0

B0 закрепил `stage2_baseline` для `FixedPred` и `Strict` в синтетической
ROCm/float32 matrix. В зарегистрированной области:

- median Strict/FixedPred device-time ratio: `2.327×`;
- peak allocated memory ratio: `1.328×`;
- `state_inference` — основная область времени;
- saved-tensor ratio в `state_inference`: `11.998×`.

Это описательный инженерный анализ, а не универсальное ranking claim.

### `SI-MA0`

`SI-MA0` проверил mechanism attribution на десяти независимо обученных моделях:

- reconstruction, observer non-interference, version coherence и comparison
  gates прошли;
- `COST-MA0` не прошёл;
- median accounting residual: приблизительно `0.1606077466` при
  зарегистрированном max-relative-residual threshold `0.05`;
- `si_ma0_passed=false`, next stage remained closed.

Отрицательный результат сохранён и не переписывается итогом `SI-MA1`.

### `SI-MA1`

`SI-MA1` использовал matched A/B/C observer calibration:

- `10` model seeds, `180` matched blocks;
- `27000` arm timing rows;
- `63000` live-region timing rows;
- `360` numerical-comparison rows;
- `180` topology-comparison rows;
- observed median `D_seed=-0.190635073373`;
- one-sided 95% bootstrap upper bound `-0.188621876160`;
- registered threshold `0.01`;
- `CAL-COST-MA1=true`, global `SI-MA1=pass`.

Signed values сохранены. Отрицательный residual является over-closure
observer calibration и не считается отрицательной физической стоимостью.
`SI-MA1` исключает future `ECZ` evaluator, action selection, fallback
validation и end-to-end B1/B2 savings.

## Теоретическое состояние

[PC-TREF Balanced Core](docs/pc-tref-balanced-core.md),
[PC-CATM](docs/pc-catm-operator-model.md),
[теоретическое основание](docs/pc-tref-pc-catm-theoretical-foundation.md) и
[ADR-013](docs/decisions/ADR-013-pc-tref-operational-semantics.md) фиксируют:

- partition-based diagnostic quotient и отдельно threshold proximity без
  предположения транзитивности;
- regret-based required equivalence;
- operational task-relative defect;
- precision-masked zero и explicit norm contracts;
- cost vector и preregistered scalarization/Pareto rule;
- разделение diagnostic-mechanism, observer и control-plane costs.

Эта фиксация выполняет теоретическое предварительное условие B1/B2. Она не
является доказательством ускорения или safety кандидатов.

## Provenance

| Артефакт | Идентификатор |
|---|---|
| B0 evidence | `stage3b-b0-evidence-v1` |
| B0 analysis | `stage3b-b0-analysis-evidence-v1` |
| `SI-MA1` preregistration | `stage3b-si-ma1-prereg-v1` |
| `SI-MA1` implementation | `stage3b-si-ma1-implementation-v1` |
| `SI-MA1` execution | `stage3b-si-ma1-confirmatory-execution-v1` |
| `SI-MA1` final | `stage3b-si-ma1-confirmatory-v1` |
| `SI-MA1` publication commit | `9bf500a2494267e83cbf9657ad2f075e349a8a75` |

Raw execution evidence и confirmatory outputs сохраняются в
`results/stage-3/si-ma1/working/confirmatory/` и
`results/stage-3/si-ma1/confirmatory/`. Документационные изменения не
пересоздают эти материалы.

## Следующий этап

После publication tag `stage3b-b1-b2-prereg-v1` разрешается отдельная
реализация B1. B2 остаётся закрытым до sealed `EQ-B1`; shared matched profiling
— до `EQ-B1` и `EQ-B2`. `EX-IF0`, `A11-OFF0`, `A11-OFF1`, predictor,
hysteresis, active control и test access требуют собственных decision gates.

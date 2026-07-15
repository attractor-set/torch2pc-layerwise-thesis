# Статус исследования

[English version](STATUS_EN.md)

Stage 1/2 завершены и остаются неизменяемой опубликованной базовой линией.
Диагностическая и статистическая публикация **Stage 3A** завершена в
validation-only области. Canonical execution, validation, sealing и публикация
**Stage 3B B0**, а также его statistical and engineering analysis завершены и
опубликованы. Полный Stage 3B остаётся незавершённым.

| Компонент | Наблюдаемый статус |
|---|---|
| Validation-only pilot | 96/96; test не вычислялся |
| Stage 1 / Stage 2 | 80/80 и 80/80 |
| Stage 2 runtime | `BP ≈ Exact < FixedPred << Strict` |
| Stage 3A same-state probes | 10/10 seeds |
| Stage 3A representation probes | 10/10 seeds |
| Exact–BP numerical controls | 10/10 seeds; 30/30 statistical control rows passed |
| Stage 3A observations | 2250 gradient; 150 representation; 750 cross-layer CKA |
| Stage 3A confirmatory statistics | 40 gradient + 20 representation comparisons |
| Stage 3A depth analysis | 180 seed-level rows; 24 statistical rows |
| Stage 3A publication figures | 8 PDF |
| Stage 3B B0 candidate | `stage2_baseline`; `FixedPred` и `Strict` |
| Stage 3B B0 lane | ROCm / float32; synthetic scaling; validation-only |
| Stage 3B B0 execution | 96/96 cells; 96 completed attempts; 0 failed |
| Process isolation | 96 process records; 96 unique child PID; fresh child per cell |
| B0 aggregate evidence | 96 cell + 480 region + 48 paired + 32 configuration rows |
| B0 integrity | non-perturbation, completeness, finite-value и SHA-256 gates passed |
| Test access Stage 3A/B0 | test dataset не использовался |
| Stage 3B B0 publication | tag/release `stage3b-b0-evidence-v1` |
| B0 analysis statistical unit | `model_seed`; 3 seeds на configuration |
| B0 analysis bounded timing | median Strict/FixedPred device time `2.327×` |
| B0 analysis bounded memory | peak allocated `1.328×`; state-inference saved tensors `11.998×` |
| B0 dominant region | `state_inference` для `FixedPred` и `Strict` |
| B0 analysis publication | tag/release `stage3b-b0-analysis-evidence-v1` |
| B0 decision gate | candidate-specific B1/B2 equivalence work: `continue` |
| Полный Stage 3B | `full_stage3b_campaign_complete=false` |
| Regression status | актуальное состояние фиксируется CI |

## Опубликованные границы результатов

### Stage 3A

Подробный отчёт опубликован в
[docs/stage3a-statistical-results.md](docs/stage3a-statistical-results.md).
Статистической единицей является независимо обученная модель; слои, batches,
параметры и samples являются повторными наблюдениями внутри model seed.

В пределах FashionMNIST, `lenet_classic`, seeds 0–9 и закреплённой реализации:

- `FixedPred` почти сохраняет направление градиента, но сильно подавляет норму
  в ранних слоях; layer 5 совпадает с BP targets;
- `Strict` в скрытых слоях расходится с BP по направлению и масштабу, а выходной
  слой близок к BP;
- представления `FixedPred` ближе к BP, чем представления `Strict`;
- gradient norm ratio возрастает с глубиной, relative L2 уменьшается;
- CKA не показывает надёжного monotonic depth trend, RSA показывает умеренный
  положительный trend.

### Stage 3B B0

B0 publication подтверждает полноту, provenance и целостность canonical
profiling baseline для candidate `stage2_baseline`. Опубликованный B0 analysis
добавляет bounded comparative findings о времени, памяти, region attribution и
scaling без расширения независимого `n` за пределы трёх model seeds на
configuration.

Зафиксировано:

- execution source `95c25d35224abd5e741f1df9327662ff2fde23ad`;
- sealing source `caa226cc1cd5d4aa0f9772c1fb997f7388d60730`;
- publication state `ed0d48063a17e2d9c6679869a4d930f933877052`;
- archive inventory
  `9abc6434b0f59b510e14ef0ad09d5c3b92a4a9472a90974cb92cdb1657e232ed`;
- seal digest
  `6a3d61838810e559a39f13e6ac39d6b22624c21d72523bddb55c33e83063c93e`;
- analysis implementation `e7a1632a947fae578e877826f0c923342669430e`;
- analysis publication state `b9ff8b2ab76f8752b15dd3bb968565d05f1fe9d3`;
- analysis publication tag `stage3b-b0-analysis-evidence-v1`.


Опубликованные bounded observations:

- median Strict/FixedPred device-time ratio — `2.327×`
  (configuration range `1.966–2.619×`);
- median Strict/FixedPred peak-allocated ratio — `1.328×`;
- `state_inference` является dominant device-time region обоих методов;
- median Strict/FixedPred saved-tensor ratio в `state_inference` — `11.998×`.

Это descriptive engineering analysis для pinned ROCm/float32 synthetic matrix.
Она не является универсальным ранжированием методов и не поддерживает
structural locality claims без дополнительных measurements.

## Публикационные артефакты

- Stage 3A [statistics](results/stage3/layerwise/confirmatory/statistics/) и
  [figures](results/stage3/layerwise/confirmatory/figures/);
- Stage 3B B0
  [sealed evidence](results/stage-3/profiling/b0/sealed-v1/);
- Stage 3B B0
  [engineering analysis](results/stage-3/profiling/b0/analysis-v1/);
- GitHub Releases
  [`stage3b-b0-evidence-v1`](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage3b-b0-evidence-v1)
  и
  [`stage3b-b0-analysis-evidence-v1`](https://github.com/attractor-set/torch2pc-layerwise-thesis/releases/tag/stage3b-b0-analysis-evidence-v1).

Committed evidence не перегенерируется при этой документационной синхронизации.

## Следующий шаг

Перейти к **Stage 3B B1/B2 candidate-specific numerical equivalence gates**:

- формализовать B1 и B2 candidates относительно опубликованного B0 baseline;
- реализовать каждый candidate отдельно;
- проверить registered cosine, relative-L2, finite-value и stability gates;
- сохранить test access выключенным;
- выполнить малый profiling pilot только для candidates, прошедших numerical
  equivalence gates;
- разрешать full matched B1/B2 profiling matrix только отдельным decision gate.

Structural locality claims остаются заблокированными до dedicated measurements
для dependency radius, graph span/lifetime, feedback operator и orchestration
barriers.

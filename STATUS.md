# Статус исследования

[English version](STATUS_EN.md)

Stage 1/2 завершены и остаются неизменяемой опубликованной базовой линией.
Диагностическая и статистическая публикация **Stage 3A** завершена в
validation-only области. Locality, profiling, exact execution и acceleration
остаются отдельными будущими подкампаниями.

| Компонент | Наблюдаемый статус |
|---|---|
| Validation-only pilot | 96/96; test не вычислялся |
| Stage 1 / Stage 2 | 80/80 и 80/80 |
| Stage 2 runtime | `BP ≈ Exact < FixedPred << Strict` |
| Stage 3A same-state probes | 10/10 seeds |
| Stage 3A representation probes | 10/10 seeds |
| Exact–BP numerical controls | 10/10 seeds; 30/30 statistical control rows passed |
| Gradient observations | 2250; cosine определён для 2250/2250 |
| Representation observations | 150; RSA определён для 150/150 |
| Cross-layer CKA observations | 750 |
| Confirmatory statistics | 40 gradient + 20 representation comparisons |
| Depth analysis | 180 seed-level rows; 24 statistical rows |
| Publication figures | 8 PDF |
| Regression suite | 120 passed |
| Evidence integrity | statistics и figures SHA256SUMS присутствуют |
| Test access Stage 3A | validation-only diagnostics; test loader не создавался |
| Расширенный Stage 3 | требует отдельных preregistration, gates и provenance chains |

## Текущая интерпретация

Подробный отчёт опубликован в
[docs/stage3a-statistical-results.md](docs/stage3a-statistical-results.md).
Статистической единицей является независимо обученная модель; слои, batches,
параметры и samples являются повторными наблюдениями внутри model seed.

В пределах FashionMNIST, `lenet_classic`, seeds 0–9 и закреплённой реализации:

- `FixedPred` почти сохраняет направление градиента, но сильно подавляет норму
  в ранних слоях; layer 5 совпадает с BP targets;
- `Strict` в скрытых слоях расходится с BP по направлению и масштабу, а
  выходной слой близок к BP;
- представления `FixedPred` ближе к BP, чем представления `Strict`, хотя обе
  группы отличаются от идеального BP target по CKA/RSA;
- gradient norm ratio возрастает с глубиной, relative L2 уменьшается;
- CKA не показывает надёжного monotonic depth trend, RSA показывает умеренный
  положительный trend.

## Публикационные артефакты

- [statistics](results/stage3/layerwise/confirmatory/statistics/): таблицы,
  `analysis_metadata.json`, `depth_analysis_metadata.json`, `SHA256SUMS`;
- [figures](results/stage3/layerwise/confirmatory/figures/): 8 PDF,
  `figure_metadata.json`, `SHA256SUMS`.

Committed evidence не перегенерируется при документационном закрытии Stage 3A.

## Следующий шаг

После merge Stage 3A publication следующий этап создаётся из обновлённого
`main` в отдельной ветке `stage3b-profiling-locality-preregistration`.
Сначала фиксируется preregistration profiling/locality с validation-only
доступом, единицей model seed, правилами warm-up/synchronization, timing и
memory attribution, locality taxonomy, failure/exclusion criteria и запретом
acceleration claims до прохождения измерительных gates.

# Stage 3B B0: статистический и инженерный анализ

[English version](report_EN.md)

## Область и статистическая единица

Анализ использует опубликованный sealed B0 evidence без повторного запуска.
Независимая единица — `model_seed`; для каждой конфигурации доступны три seeds.
Поэтому результаты являются описательными инженерными оценками. Cells, regions,
steps и repetitions не увеличивают независимое `n`, а дискретные p-values при
`n=3` не используются для утверждений о превосходстве.

Граница публикации сохраняется:

- `full_b0_campaign_complete=true`;
- `full_stage3b_campaign_complete=false`;
- test dataset не использовался.

## Strict относительно FixedPred

Медиана configuration-level отношения Strict/FixedPred составила:

| Метрика | Медиана | Диапазон по конфигурациям |
|---|---:|---:|
| Device time | 2.327× | 1.966–2.619× |
| Host time | 2.327× | 1.969–2.619× |
| Peak allocated memory | 1.328× | 1.068–2.160× |
| Peak reserved memory | 1.323× | 1.064–2.058× |

Во всех configuration medians Strict дороже FixedPred по времени и peak memory.
Это bounded observation для synthetic scaling family, ROCm/float32 и закреплённой
реализации, а не универсальное ранжирование методов.

## Attribution узких мест

Для нормализации использована доля от суммы median времени пяти regions внутри
cell. Region medians не предполагаются аддитивными к composite median.

| Метод | Dominant region | State inference | VJP regions | Amdahl proxy |
|---|---|---:|---:|---:|
| FixedPred | `state_inference` | 71.8% | 26.7% | 1.364× |
| Strict | `state_inference` | 78.8% | 20.5% | 1.258× |

`state_inference` является главным device-time region для обоих методов. VJP
proxy превышает preregistered continuation thresholds, но является только
верхней инженерной границей при гипотетическом устранении нормализованной доли
`local_state_vjp + parameter_vjp`.

Saved tensors в `state_inference`:

| Метод | Median mean saved-tensor bytes | MiB |
|---|---:|---:|
| FixedPred | 3352832 | 3.20 |
| Strict | 40227920 | 38.36 |

Отношение Strict/FixedPred равно
`11.998×`. Это указывает
на отдельный graph-retention/memory bottleneck внутри `state_inference`, но не
заменяет peak allocated/reserved analysis.

## Масштабирование

Медианные множители на удвоение фактора из seed-level log2 main-effect models:

| Метод | Метрика | Depth | Width | Batch size |
|---|---|---:|---:|---:|
| FixedPred | Device time | 1.941× | 0.998× | 0.999× |
| Strict | Device time | 2.089× | 1.000× | 1.001× |
| FixedPred | Peak allocated | 1.544× | 2.097× | 1.237× |
| Strict | Peak allocated | 1.384× | 2.084× | 1.399× |

Модели не содержат interaction terms и используются как компактная
чувствительность инженерной матрицы, а не как универсальный закон сложности.

## Locality boundary

Опубликованные B0 aggregates поддерживают region-cost attribution, но не содержат
полный structural locality contract: dependency radius, graph span/modules,
independent lifetime, feedback operator и orchestration barriers. Поэтому
утверждения о многомерной локальности остаются заблокированными.

## Decision gate

- B1/B2 candidate-specific equivalence work: **continue**;
- full B1/B2 matched profiling: **blocked_pending_candidate_specific_gates**;
- locality claims: **blocked_by_missing_structural_evidence**;
- новый B0 execution: **not_required**.

Решение разрешает только реализацию и candidate-specific numerical gates.
Полный Stage 3B и comparative candidate profiling остаются незавершёнными.

## Артефакты

- `paired_configuration_summary.csv`;
- `paired_matrix_summary.csv`;
- `region_seed_attribution.csv`;
- `region_configuration_summary.csv`;
- `region_matrix_summary.csv`;
- `region_paired_configuration_summary.csv`;
- `scaling_seed_effects.csv`;
- `scaling_summary.csv`;
- четыре PDF figure;
- `analysis_summary.json`, `analysis_metadata.json`, `SHA256SUMS`.

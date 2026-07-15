"""Bilingual bounded reports for Stage 3B B0 engineering analysis."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pandas as pd

REPORT_FILENAMES = ("report.md", "report_EN.md")


def _as_float(value: object) -> float:
    return float(cast(float | int | str, value))


def _ratio(summary: dict[str, object], metric: str) -> tuple[float, float, float]:
    paired = cast(dict[str, object], summary["paired_strict_relative_to_fixedpred"])
    record = cast(dict[str, object], paired[metric])
    return (
        _as_float(record["configuration_median_ratio"]),
        _as_float(record["configuration_min_ratio"]),
        _as_float(record["configuration_max_ratio"]),
    )


def _bottleneck(summary: dict[str, object], method: str) -> dict[str, object]:
    bottlenecks = cast(dict[str, object], summary["bottlenecks"])
    return cast(dict[str, object], bottlenecks[method])


def _scaling_value(
    scaling: pd.DataFrame,
    *,
    method: str,
    metric: str,
    factor: str,
) -> float:
    row = scaling.loc[
        (scaling["method"] == method)
        & (scaling["metric"] == metric)
        & (scaling["factor"] == factor)
    ]
    return float(row["multiplier_per_doubling_median"].iloc[0])


def _render_ru(summary: dict[str, object], scaling: pd.DataFrame) -> str:
    device = _ratio(summary, "device_time")
    host = _ratio(summary, "host_time")
    allocated = _ratio(summary, "peak_allocated")
    reserved = _ratio(summary, "peak_reserved")
    fixedpred = _bottleneck(summary, "fixedpred")
    strict = _bottleneck(summary, "strict")
    decision = cast(dict[str, object], summary["decision_gate"])
    saved = cast(dict[str, object], summary["saved_tensor_analysis"])
    return f"""# Stage 3B B0: статистический и инженерный анализ

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
| Device time | {device[0]:.3f}× | {device[1]:.3f}–{device[2]:.3f}× |
| Host time | {host[0]:.3f}× | {host[1]:.3f}–{host[2]:.3f}× |
| Peak allocated memory | {allocated[0]:.3f}× | {allocated[1]:.3f}–{allocated[2]:.3f}× |
| Peak reserved memory | {reserved[0]:.3f}× | {reserved[1]:.3f}–{reserved[2]:.3f}× |

Во всех configuration medians Strict дороже FixedPred по времени и peak memory.
Это bounded observation для synthetic scaling family, ROCm/float32 и закреплённой
реализации, а не универсальное ранжирование методов.

## Attribution узких мест

Для нормализации использована доля от суммы median времени пяти regions внутри
cell. Region medians не предполагаются аддитивными к composite median.

| Метод | Dominant region | State inference | VJP regions | Amdahl proxy |
|---|---|---:|---:|---:|
| FixedPred | `{fixedpred['dominant_device_region']}` | {_as_float(fixedpred['state_inference_share_median']):.1%} | {_as_float(fixedpred['vjp_region_share_median']):.1%} | {_as_float(fixedpred['vjp_region_amdahl_upper_bound_proxy']):.3f}× |
| Strict | `{strict['dominant_device_region']}` | {_as_float(strict['state_inference_share_median']):.1%} | {_as_float(strict['vjp_region_share_median']):.1%} | {_as_float(strict['vjp_region_amdahl_upper_bound_proxy']):.3f}× |

`state_inference` является главным device-time region для обоих методов. VJP
proxy превышает preregistered continuation thresholds, но является только
верхней инженерной границей при гипотетическом устранении нормализованной доли
`local_state_vjp + parameter_vjp`.

Saved tensors в `state_inference`:

| Метод | Median mean saved-tensor bytes | MiB |
|---|---:|---:|
| FixedPred | {_as_float(saved['state_inference_fixedpred_bytes_mean_median']):.0f} | {_as_float(saved['state_inference_fixedpred_bytes_mean_median']) / (1024 ** 2):.2f} |
| Strict | {_as_float(saved['state_inference_strict_bytes_mean_median']):.0f} | {_as_float(saved['state_inference_strict_bytes_mean_median']) / (1024 ** 2):.2f} |

Отношение Strict/FixedPred равно
`{_as_float(saved['state_inference_strict_to_fixedpred_ratio']):.3f}×`. Это указывает
на отдельный graph-retention/memory bottleneck внутри `state_inference`, но не
заменяет peak allocated/reserved analysis.

## Масштабирование

Медианные множители на удвоение фактора из seed-level log2 main-effect models:

| Метод | Метрика | Depth | Width | Batch size |
|---|---|---:|---:|---:|
| FixedPred | Device time | {_scaling_value(scaling, method='fixedpred', metric='device_time', factor='depth'):.3f}× | {_scaling_value(scaling, method='fixedpred', metric='device_time', factor='width'):.3f}× | {_scaling_value(scaling, method='fixedpred', metric='device_time', factor='batch_size'):.3f}× |
| Strict | Device time | {_scaling_value(scaling, method='strict', metric='device_time', factor='depth'):.3f}× | {_scaling_value(scaling, method='strict', metric='device_time', factor='width'):.3f}× | {_scaling_value(scaling, method='strict', metric='device_time', factor='batch_size'):.3f}× |
| FixedPred | Peak allocated | {_scaling_value(scaling, method='fixedpred', metric='peak_allocated', factor='depth'):.3f}× | {_scaling_value(scaling, method='fixedpred', metric='peak_allocated', factor='width'):.3f}× | {_scaling_value(scaling, method='fixedpred', metric='peak_allocated', factor='batch_size'):.3f}× |
| Strict | Peak allocated | {_scaling_value(scaling, method='strict', metric='peak_allocated', factor='depth'):.3f}× | {_scaling_value(scaling, method='strict', metric='peak_allocated', factor='width'):.3f}× | {_scaling_value(scaling, method='strict', metric='peak_allocated', factor='batch_size'):.3f}× |

Модели не содержат interaction terms и используются как компактная
чувствительность инженерной матрицы, а не как универсальный закон сложности.

## Locality boundary

Опубликованные B0 aggregates поддерживают region-cost attribution, но не содержат
полный structural locality contract: dependency radius, graph span/modules,
independent lifetime, feedback operator и orchestration barriers. Поэтому
утверждения о многомерной локальности остаются заблокированными.

## Decision gate

- B1/B2 candidate-specific equivalence work: **{decision['b1_b2_candidate_specific_equivalence_work']}**;
- full B1/B2 matched profiling: **{decision['full_b1_b2_matched_profiling']}**;
- locality claims: **{decision['locality_claims']}**;
- новый B0 execution: **{decision['new_b0_execution']}**.

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
"""


def _render_en(summary: dict[str, object], scaling: pd.DataFrame) -> str:
    device = _ratio(summary, "device_time")
    host = _ratio(summary, "host_time")
    allocated = _ratio(summary, "peak_allocated")
    reserved = _ratio(summary, "peak_reserved")
    fixedpred = _bottleneck(summary, "fixedpred")
    strict = _bottleneck(summary, "strict")
    decision = cast(dict[str, object], summary["decision_gate"])
    saved = cast(dict[str, object], summary["saved_tensor_analysis"])
    return f"""# Stage 3B B0: statistical and engineering analysis

[Русская версия](report.md)

## Scope and statistical unit

The analysis reads the published sealed B0 evidence without rerunning the
campaign. The independent unit is `model_seed`, with three seeds per
configuration. Results are therefore descriptive engineering estimates. Cells,
regions, steps, and repetitions do not increase the independent `n`, and
discrete p-values at `n=3` are not used for superiority claims.

The publication boundary remains:

- `full_b0_campaign_complete=true`;
- `full_stage3b_campaign_complete=false`;
- the test dataset was not accessed.

## Strict relative to FixedPred

The median configuration-level Strict/FixedPred ratio was:

| Metric | Median | Configuration range |
|---|---:|---:|
| Device time | {device[0]:.3f}× | {device[1]:.3f}–{device[2]:.3f}× |
| Host time | {host[0]:.3f}× | {host[1]:.3f}–{host[2]:.3f}× |
| Peak allocated memory | {allocated[0]:.3f}× | {allocated[1]:.3f}–{allocated[2]:.3f}× |
| Peak reserved memory | {reserved[0]:.3f}× | {reserved[1]:.3f}–{reserved[2]:.3f}× |

Strict is more expensive than FixedPred in every configuration median for time
and peak memory. This is a bounded observation for the synthetic scaling family,
ROCm/float32, and the pinned implementation rather than a universal ranking.

## Bottleneck attribution

The analysis normalizes each region by the sum of the five region medians within
the cell. Region medians are not assumed to be additive to the composite median.

| Method | Dominant region | State inference | VJP regions | Amdahl proxy |
|---|---|---:|---:|---:|
| FixedPred | `{fixedpred['dominant_device_region']}` | {_as_float(fixedpred['state_inference_share_median']):.1%} | {_as_float(fixedpred['vjp_region_share_median']):.1%} | {_as_float(fixedpred['vjp_region_amdahl_upper_bound_proxy']):.3f}× |
| Strict | `{strict['dominant_device_region']}` | {_as_float(strict['state_inference_share_median']):.1%} | {_as_float(strict['vjp_region_share_median']):.1%} | {_as_float(strict['vjp_region_amdahl_upper_bound_proxy']):.3f}× |

`state_inference` is the dominant device-time region for both methods. The VJP
proxy exceeds the preregistered continuation thresholds, but it is only an
engineering upper bound under hypothetical removal of the normalized
`local_state_vjp + parameter_vjp` share.

Saved tensors in `state_inference`:

| Method | Median mean saved-tensor bytes | MiB |
|---|---:|---:|
| FixedPred | {_as_float(saved['state_inference_fixedpred_bytes_mean_median']):.0f} | {_as_float(saved['state_inference_fixedpred_bytes_mean_median']) / (1024 ** 2):.2f} |
| Strict | {_as_float(saved['state_inference_strict_bytes_mean_median']):.0f} | {_as_float(saved['state_inference_strict_bytes_mean_median']) / (1024 ** 2):.2f} |

The Strict/FixedPred ratio is
`{_as_float(saved['state_inference_strict_to_fixedpred_ratio']):.3f}×`. This
identifies a separate graph-retention/memory bottleneck inside
`state_inference`, while remaining distinct from peak allocated/reserved memory.

## Scaling

Median per-doubling multipliers from seed-level log2 main-effect models:

| Method | Metric | Depth | Width | Batch size |
|---|---|---:|---:|---:|
| FixedPred | Device time | {_scaling_value(scaling, method='fixedpred', metric='device_time', factor='depth'):.3f}× | {_scaling_value(scaling, method='fixedpred', metric='device_time', factor='width'):.3f}× | {_scaling_value(scaling, method='fixedpred', metric='device_time', factor='batch_size'):.3f}× |
| Strict | Device time | {_scaling_value(scaling, method='strict', metric='device_time', factor='depth'):.3f}× | {_scaling_value(scaling, method='strict', metric='device_time', factor='width'):.3f}× | {_scaling_value(scaling, method='strict', metric='device_time', factor='batch_size'):.3f}× |
| FixedPred | Peak allocated | {_scaling_value(scaling, method='fixedpred', metric='peak_allocated', factor='depth'):.3f}× | {_scaling_value(scaling, method='fixedpred', metric='peak_allocated', factor='width'):.3f}× | {_scaling_value(scaling, method='fixedpred', metric='peak_allocated', factor='batch_size'):.3f}× |
| Strict | Peak allocated | {_scaling_value(scaling, method='strict', metric='peak_allocated', factor='depth'):.3f}× | {_scaling_value(scaling, method='strict', metric='peak_allocated', factor='width'):.3f}× | {_scaling_value(scaling, method='strict', metric='peak_allocated', factor='batch_size'):.3f}× |

The models omit interaction terms and are compact engineering-matrix
sensitivities rather than universal complexity laws.

## Locality boundary

Published B0 aggregates support region-cost attribution but do not contain the
full structural locality contract: dependency radius, graph span/modules,
independent lifetime, feedback operator, and orchestration barriers. Claims
about multidimensional locality therefore remain blocked.

## Decision gate

- B1/B2 candidate-specific equivalence work: **{decision['b1_b2_candidate_specific_equivalence_work']}**;
- full B1/B2 matched profiling: **{decision['full_b1_b2_matched_profiling']}**;
- locality claims: **{decision['locality_claims']}**;
- new B0 execution: **{decision['new_b0_execution']}**.

The decision authorizes implementation and candidate-specific numerical gates
only. Full Stage 3B and comparative candidate profiling remain incomplete.

## Artifacts

- `paired_configuration_summary.csv`;
- `paired_matrix_summary.csv`;
- `region_seed_attribution.csv`;
- `region_configuration_summary.csv`;
- `region_matrix_summary.csv`;
- `region_paired_configuration_summary.csv`;
- `scaling_seed_effects.csv`;
- `scaling_summary.csv`;
- four PDF figures;
- `analysis_summary.json`, `analysis_metadata.json`, and `SHA256SUMS`.
"""


def write_b0_reports(
    summary: dict[str, object],
    paired_configurations: pd.DataFrame,
    region_summary: pd.DataFrame,
    scaling_summary: pd.DataFrame,
    output_root: Path,
) -> dict[str, int]:
    """Write bounded Russian and English reports."""

    del paired_configurations, region_summary
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / REPORT_FILENAMES[0]).write_text(
        _render_ru(summary, scaling_summary), encoding="utf-8"
    )
    (output_root / REPORT_FILENAMES[1]).write_text(
        _render_en(summary, scaling_summary), encoding="utf-8"
    )
    return {filename: 1 for filename in REPORT_FILENAMES}

# Stage 3B B0: pipeline статистического и инженерного анализа

[English version](stage3b-b0-analysis-pipeline_EN.md)

## Назначение

`stage3b_b0_analysis.py` реализует read-only анализ опубликованного
`sealed-v1`. CLI:

```bash
python scripts/analyze_stage3b_b0.py \
  --evidence-root results/stage-3/profiling/b0/sealed-v1 \
  --output-root results/stage-3/profiling/b0/analysis-v1 \
  --source-commit <merged-analysis-implementation-commit> \
  --generated-at-utc <frozen-UTC-timestamp>
```

## Gates

До расчётов pipeline проверяет:

- точное соответствие `SHA256SUMS`;
- отсутствие missing/unexpected files;
- published seal claim boundary;
- 96 cells, 480 region rows, 48 pairs и 32 configuration rows;
- полную factorial matrix и три seeds на конфигурацию;
- integrity flags и отсутствие non-finite events.

После записи outputs sealed input проверяется повторно. Output внутри
`sealed-v1` запрещён.

## Аналитические ограничения

- statistical unit: `model_seed`;
- independent `n=3` per configuration;
- p-values не используются для superiority claims;
- configuration matrix анализируется описательно;
- region shares нормализуются внутри суммы region medians;
- scaling models не включают interactions;
- full Stage 3B остаётся incomplete.

## Software/evidence separation

Рекомендуется два коммита:

1. software commit с module, CLI, tests и frozen analysis contract;
2. после merge — отдельный evidence commit с generated `analysis-v1`.

Это позволяет metadata фиксировать merged analysis implementation commit и
проверять exact committed tree до публикации.

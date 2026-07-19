# Доказательный контур сопоставленного этапа 3B

[English version](stage3b-matched-evidence_EN.md)

## Артефакты одной ячейки

Каждая успешно завершённая [попытка](glossary.md#term-attempt) содержит:

- `request.json`;
- `started.json`;
- `resolved-config.json`;
- `environment.json`;
- `measurements.json`;
- `locality-events.jsonl`;
- `completed.json`.

В `measurements.json` раздельно сохраняются:

- `primary_timing_measurements` для режима `no_hooks`;
- `structural_timing_measurements` для режима `counters_only`;
- `observer_cost_measurements`;
- `region_measurements`;
- `structural_measurements`;
- `integrity_measurements`.

[Стоимость наблюдателя](glossary.md#term-observer-cost) не вычитается из основного времени.

## Проверка и фиксация

Проверка без создания доказательного пакета:

```bash
python scripts/seal_stage3b_matched.py \
  --validate-only \
  --runtime-root "$OUTPUT_ROOT" \
  --matched-manifest \
    experiments/planned/STAGE3B-B1-B2-MATCHED-PROFILING-MANIFEST.json \
  --expected-source-commit "$PROJECT_SOURCE_COMMIT" \
  --expected-image-digest "$IMAGE_DIGEST" \
  --expected-authorization-token "$AUTHORIZATION_TOKEN"
```

Фиксация выполняется только из чистого коммита в новый пустой каталог. Она
создаёт таблицы ячеек и повторов, поток событий локальности, сводную таблицу,
метаданные анализа, описание среды, реестр исходных файлов, `seal.json` и
`SHA256SUMS`.

Фиксация устанавливает `evidence=true`, но сохраняет
`results_publication_permitted=false`.

## Анализ

```bash
python scripts/analyze_stage3b_matched.py \
  --evidence-root <sealed-root> \
  --output-root <new-analysis-root>
```

Кандидаты сравниваются с `stage2_baseline` внутри одного сопоставленного
блока. Шаги сворачиваются до повторов, повторы до ячеек, после чего строятся
описательные сводки по начальным состояниям модели. При `n=3` не создаются
значения `p` и утверждения о превосходстве.

Инженерная пригодность к продолжению не открывает `EX-IF0` и не разрешает
активацию политики.

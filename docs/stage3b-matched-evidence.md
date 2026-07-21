# Доказательный контур сопоставленного этапа 3B

[English version](stage3b-matched-evidence_EN.md)

Этот документ описывает границу артефактов после ADR-015.

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
    experiments/frozen/stage3b-matched-profiling-v2/manifest.json \
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

Завершённый пакет [доказательных материалов](glossary.md#term-evidence)
сохранён в:

```text
results/stage-3/profiling/matched/
  stage3b-matched-profiling-e1dcfb2-v1/
```

Он содержит 288 ячеек, 1440 строк повторов, 96 сводок сопоставленных блоков,
288 неизменяемых историй попыток, 96 неизмеряемых записей межкандидатной
корректности, события локальности для каждой ячейки, фиксацию среды и реестр
[времени выполнения](glossary.md#term-runtime). Сохранение не открывает
описательный анализ.

После PR сохранения доказательных материалов и зелёного CI тег
`stage3b-matched-profiling-evidence-v1` создаёт только черновой `GitHub Release`.
Репозиторные активы формируются командой
`scripts/package_stage3b_matched_release.py --mode repository`; локальный режим
`--mode full` дополнительно упаковывает контрольный контур, артефакты запуска,
контрольную запись образа и журналы фиксации из проверенной внешней записи
происхождения релиза. Публичная публикация релиза остаётся запрещённой.

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

## Исправительный допуск перед новой кампанией из 288 ячеек

После `ADR-017` производственное [выполнение](glossary.md#term-execution) закрывается при любой ошибке. Новая
фиксация среды и авторизация не заменяют научный допуск. Перед запуском
одновременно требуются:

- подтверждающий `EQ-B1`: `120/120` сопоставленных пар;
- подтверждающий `EQ-B2`: `120/120` троек и `240/240` сравнений;
- точная балансировка порядка кандидатов для каждого метода: шесть перестановок
  по восемь раз, `16/16/16` по позициям и `24/24` по попарному предшествованию;
- отдельная неизмеряемая запись межкандидатной корректности для каждого блока
  профилирования;
- новый пустой корень результатов, новый неизменяемый образ и новая
  авторизация.

Повтор допускается только для записей с `retry_eligible=true` и классом
`infrastructure`, `operator_interruption` или `system_interruption`. Научные,
неизвестные ошибки и ошибки корректности блокируют повтор и фиксацию. Фиксация
сохраняет `attempt-history.jsonl` и `block-correctness.jsonl`; успешная попытка
должна быть ровно одна и последняя.

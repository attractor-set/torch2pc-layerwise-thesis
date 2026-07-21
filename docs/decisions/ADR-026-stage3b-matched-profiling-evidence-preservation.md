# ADR-026: сохранение доказательных материалов сопоставленного профилирования и черновой релиз

[English version](ADR-026-stage3b-matched-profiling-evidence-preservation_EN.md)

- **Статус:** принято
- **Дата:** 21 июля 2026 года

## Контекст

Новый пакет `v2` [сопоставленного профилирования](../glossary.md#term-matched-profiling)
был перспективно связан с запечатанными допусками `EQ-B1` и `EQ-B2`.
После создания неизменяемого образа, отдельной проверки ROCm/float32,
авторизации, неизмеряемого плана и проверки всех границ [выполнение](../glossary.md#term-execution)
охватило ровно 288 ячеек в 96 сопоставленных блоках. Все попытки завершились
успешно, повтор не потребовался, а проверка [среды выполнения](../glossary.md#term-runtime)
подтвердила полный и согласованный контур.

Отдельная [фиксация целостности](../glossary.md#term-integrity-sealing)
сформировала компактный набор [доказательных материалов](../glossary.md#term-evidence).
Фиксация установила `evidence=true`, но сохранила
`results_publication_permitted=false` и
`full_stage3b_campaign_complete=false`. Следовательно, сохранение набора не
разрешает описательный анализ, публикацию результатов или следующий
экспериментальный этап.

## Решение

Побайтно сохранить запечатанный набор в:

```text
results/stage-3/profiling/matched/
  stage3b-matched-profiling-e1dcfb2-v1/
```

Репозиторий сохраняет без потерь сжатое представление ровно в 13 файлах:

```text
SHA256SUMS
SEALED-SHA256SUMS
analysis_metadata.json
attempt-history.jsonl
block-correctness.jsonl
environment-lock.json
locality_events.asset.json
locality_events.jsonl.zst
profiling_cells.csv
profiling_repetitions.csv
profiling_summary.csv
runtime-inventory.json
seal.json
```

`SEALED-SHA256SUMS` является побайтно неизменным реестром, созданным при
фиксации. Поток `locality_events.jsonl` размером 6,09 ГиБ сохраняется без
потерь в архиве формата `Zstandard` размером 23,9 МиБ.
`locality_events.asset.json` связывает SHA-256 сжатого и исходного потоков,
исходный размер, параметры сжатия и имя актива чернового релиза. Остальные
запечатанные файлы остаются побайтно неизменными.

`seal.json` обязан фиксировать:

```text
scope=stage3b_b1_b2_matched_sealed_evidence_v1
status=sealed
source_commit=e1dcfb26823e1191b98d2aa2a598499b13197583
image_digest=sha256:3c269b4278026b5b69968b3265b506ce626f2baf693859989de3371d639da4d0
matched_cell_count=288
attempt_history_count=288
cross_candidate_correctness_block_count=96
retried_cell_count=0
evidence=true
full_lane_complete=true
full_stage3b_campaign_complete=false
results_publication_permitted=false
test_dataset_access=false
```

Кандидаты должны быть представлены симметрично: по 96 ячеек для
`stage2_baseline`, `isolated_layer_vjp` и `composite_vjp`. Таблица повторов
содержит 1440 строк, сводная таблица — 96 строк, а поток событий локальности
покрывает все 288 ячеек.

## Граница после сохранения

После этого PR машинно-проверяемая граница имеет вид:

```text
matched_profiling_execution_open=false
matched_profiling_execution_complete=true
matched_profiling_runtime_validation=valid
matched_profiling_evidence=sealed
matched_profiling_analysis_open=false
runtime_authorization=issued_consumed
measurements_allowed=false
results_publication_permitted=false
release_draft_required=true
release_publication_permitted=false
full_stage3b_campaign_complete=false
test_dataset_access=false
```

Авторизация считается использованной и не разрешает новое
[выполнение](../glossary.md#term-execution). Для любой новой измерительной
кампании требуется новый пустой корень результатов и отдельная авторизация.

## Релизный контур

После слияния PR сохранения доказательных материалов и успешного CI создаётся неизменяемый тег:

```text
stage3b-matched-profiling-evidence-v1
```

Специальный процесс GitHub Actions создаёт только **черновой** `GitHub Release`.
Репозиторная часть релиза включает компактный архив доказательных материалов,
отдельный без потерь сжатый актив `locality_events` в формате `Zstandard`,
`RELEASE-MANIFEST.json`, `RELEASE-NOTES.md` и `SHA256SUMS`.

Локальный упаковщик дополнительно может подготовить:

```text
stage3b-matched-profiling-control-plane-v1.tar.gz
stage3b-matched-profiling-runtime-records-v1.tar.gz
stage3b-matched-profiling-image-checkpoint-v1.tar.gz
stage3b-matched-profiling-sealing-logs-v1.tar.gz
stage3b-matched-profiling-release-source-record-v1.json
```

Эти активы строятся только из ранее проверенного внешнего
`release-source-record.json`. Упаковщик проверяет контрольный контур,
неизмеряемый план, полный журнал выполнения, образ и журналы фиксации. Он не
изменяет [доказательные материалы](../glossary.md#term-evidence) и не публикует релиз.

Пока `release_publication_permitted=false`, процесс GitHub Actions и локальный
упаковщик обязаны сохранять релиз в черновом состоянии. Публикация требует
отдельного решения после описательного анализа и проверки границы публикации.

## Последствия

### Положительные

- полный вычислительный [запуск](../glossary.md#term-run) становится проверяемым репозиторным артефактом без сохранения Git-объекта размером 6,09 ГиБ;
- 288 ячеек и 96 блоков связаны с точным образом, исходным коммитом и
  неизменяемым реестром файлов;
- артефакты запуска могут быть приложены к черновому `GitHub Release` без
  включения громоздкого исходного дерева среды выполнения в Git;
- описательный анализ сможет использовать только опубликованный запечатанный каталог.

### Ограничения

- сохранение [доказательных материалов](../glossary.md#term-evidence) не является результатом сравнительного анализа;
- утверждения о превосходстве B1 или B2 пока запрещены;
- `EX-IF0`, политики `ECZ`/`NCZ`, `A11-OFF0`, `A11-OFF1` и `QWake-PC` остаются
  закрытыми;
- тестовая выборка не открывается;
- публичный релиз запрещён до отдельной границы допуска к публикации.

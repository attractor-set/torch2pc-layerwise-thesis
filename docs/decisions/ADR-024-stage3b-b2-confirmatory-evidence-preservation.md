# ADR-024: фиксация подтверждающих доказательных материалов этапа 3B B2

[English version](ADR-024-stage3b-b2-confirmatory-evidence-preservation_EN.md)

- **Статус:** принято
- **Дата:** 20 июля 2026 года

## Контекст

Подтверждающий контракт B2 был предварительно зарегистрирован как 120
сопоставленных троек и 240 прямых сравнений для `FixedPred` и `Strict` в
контурах CPU `float64` и ROCm `float32`. После заморозки запроса,
проверок среды, закрытых при ошибке, отдельной инженерной проверки и неизмеряемого
полного плана были выполнены все 120 троек. Жизненный цикл попыток завершился
без неудачных троек, а `EQ-B2-CONFIRMATORY` был запечатан с положительным
решением.

Производное решение `EQ-B2` связано с подтверждающим решением его SHA-256 и
не создаётся из инженерной проверки. Тестовая выборка не использовалась.

## Решение

Сохранить побайтно запечатанный набор в:

```text
results/stage-3/b2/stage3b-b2-confirmatory-63885e5-v1/
```

Набор содержит только следующие 11 файлов:

```text
SHA256SUMS
attempt-history.jsonl
authorization.json
decision.json
direct-b1-b2-metrics.csv
endpoint-metrics.csv
matched-profiling-admission.json
request.json
resolved-config.json
structural-events.jsonl
trajectory-metrics.csv
```

`decision.json` обязан фиксировать:

```text
decision_id=EQ-B2-CONFIRMATORY
scope=confirmatory
status=pass
sealed=true
matched_triples_expected=120
matched_triples_observed=120
pairwise_comparisons_expected=240
pairwise_comparisons_observed=240
failed_pair_count=0
failed_pairs=[]
failed_triples=[]
dangerous_misses=0
test_dataset_access=false
results_publication_permitted=false
```

Все пять зарегистрированных проверок — `STRUCT-B2`, `NUM-B2`, `TRAJ-B2`,
`OBS-B2` и `PROV-B2` — должны иметь `passed=true` и пустой список неудачных
троек.

`matched-profiling-admission.json` обязан фиксировать производное решение
`EQ-B2`, ссылаться на `EQ-B2-CONFIRMATORY`, содержать SHA-256
`decision.json` и повторять положительные показатели без ретроспективного
изменения исходного решения.

## Граница допуска

Положительный подтверждающий B2 завершает научную цепочку допуска B1/B2, но
не разрешает использование прежнего запроса сопоставленного [профилирования](../glossary.md#term-profiling).
Он был создан до подтверждающего B2 и сохраняется только как исторический
артефакт.

Следующий допустимый переход:

```text
sealed EQ-B1 + sealed EQ-B2
→ новый версионированный matched-profiling request/manifest freeze
→ отдельные image/preflight/authorization/dry-run gates
→ только затем 288-cell execution
```

После данного PR граница остаётся закрытой:

```text
scientific_admission=open_after_eq_b2_confirmatory
matched_profiling_request_refresh_required=true
matched_profiling_execution_open=false
runtime_authorization=not_issued
measurements_allowed=false
test_dataset_access=false
```

Ни сохранение [доказательных материалов](../glossary.md#term-evidence), ни производный `EQ-B2` не разрешают [сопоставленное профилирование](../glossary.md#term-matched-profiling),
`EX-IF0`, `A11-OFF0`, `A11-OFF1`, оцениватель, `QWake-PC` или доступ к тестовой
выборке.

## Целостность и воспроизводимость

- `SHA256SUMS` проверяет каждый содержательный файл запечатанного набора;
- `attempt-history.jsonl` содержит ровно 120 завершённых записей и 120
  уникальных `triple_id`;
- агрегированные файлы содержат 120 троек и 240 прямых сравнений;
- `structural-events.jsonl` содержит 1800 событий: 600 для `FixedPred` и 1200
  для `Strict`;
- авторизация до фиксации сохраняет `evidence=false`; научным доказательным материалом
  является только положительно запечатанное решение и связанный с ним набор;
- ранее опубликованные B1, инженерная проверка B2 и артефакты сопоставленного профилирования не
  переписываются.

## Последствия

### Положительные

- подтверждающая эквивалентность B2 становится проверяемым репозиторным
  артефактом;
- цепочка допуска B1/B2 завершена без использования тестовой выборки;
- новая фиксация сопоставленного профилирования может быть подготовлена перспективно.

### Ограничения

- полный этап 3B всё ещё не завершён;
- производительность B2 ещё не измерена в новой кампании из 288 ячеек;
- прежние `request`/`manifest` сопоставленного профилирования не получает допуска задним
  числом;
- [доказательные материалы](../glossary.md#term-evidence) нельзя использовать как универсальное доказательство вне
  зарегистрированных моделей, начальных значений, пакетов, методов, типов данных и среды.

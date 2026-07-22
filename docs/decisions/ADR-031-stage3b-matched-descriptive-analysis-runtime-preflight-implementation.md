# ADR-031: реализация предварительной проверки среды описательного анализа `Stage 3B`

[English version](ADR-031-stage3b-matched-descriptive-analysis-runtime-preflight-implementation_EN.md)

- **Статус:** принято
- **Дата:** 2026-07-21

## Контекст

ADR-030 зафиксировал запрос одного будущего [запуска](../glossary.md#term-run),
но не зафиксировал [среду выполнения](../glossary.md#term-runtime) и не выдал
`authorization`. До отдельного допуска нужен проверяемый контур, который
связывает состояние репозитория, исполняемые файлы Python и `Zstandard`,
версии и модули `NumPy` и `Matplotlib`, неизменяемые входы и отсутствующий
выходной каталог, не читая наблюдённые значения метрик.

## Решение

Добавить отдельный модуль предварительной проверки среды и два узких `CLI`:

- `preflight_stage3b_matched_analysis.py` формирует только файл
  `runtime-preflight.json`;
- `execute_stage3b_matched_analysis.py` не принимает путь к внешнему
  `authorization` или время генерации и использует только будущий `frozen`
  пакет по каноническому пути;
- `verifier` требует точное связывание `request_digest`, `preflight_digest`,
  `runtime_identity_digest`, `generated_at_utc`, единственного `output root` и
  операторского подтверждения;
- `verifier` принимает только точный трёхфайловый пакет из обычных файлов,
  отклоняя символические ссылки, каталоги, дополнительные записи и дубликаты
  в `SHA256SUMS`;
- `executor` до вычисления атомарно создаёт квитанцию: одна
  [попытка](../glossary.md#term-attempt) для `request_digest` считается
  использованной; затем он запускает ядро только во временном каталоге,
  повторно проверяет входные SHA-256 и лишь затем атомарно публикует
  канонический `output root`.

Предварительная проверка вычисляет только SHA-256, проверяет чистый Git,
идентичность исполняемых файлов и прямых численных зависимостей, отсутствие
`output root` и целостность кадра `Zstandard`. Значения `CSV`/`JSONL` метрик
не разбираются.

## Граница решения

```text
runtime_preflight_implemented=true
runtime_preflight_artifact_frozen=false
execution_authorization_present=false
analysis_execution_permitted=false
analysis_execution_performed=false
analysis_results_present=false
results_publication_permitted=false
release_publication_permitted=false
```

В репозиторий не добавляется пакет `authorization`; публичный `executor` остаётся
закрытым до отдельного `merge`.

## Последствия

Положительные:

- `runtime identity` можно зафиксировать после `merge` без циклической зависимости
  от ещё неизвестного `merge commit`;
- внешний или подменённый `authorization` не может быть передан через `CLI`;
- повторная попытка по тому же `request_digest` закрывается атомарно
  созданной локальной квитанцией, даже если `output root` был удалён;
- канонический `output root` появляется только после повторной проверки
  входных SHA-256;
- `generated_at_utc` берётся только из `frozen authorization` и не может
  предшествовать времени предварительной проверки `runtime`.

Ограничения:

- фактическая предварительная проверка `runtime` ещё не зафиксирована;
- `authorization` ещё не выдан;
- запечатанные [доказательные материалы](../glossary.md#term-evidence) не
  анализируются;
- квитанция единственной попытки относится к каноническому Git-клону; будущая
  процедура `authorization` обязана явно зафиксировать это рабочее пространство
  выполнения;
- черновой релиз остаётся неопубликованным.

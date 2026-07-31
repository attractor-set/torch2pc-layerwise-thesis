# ADR-092: реализация адаптера вызова материализации финального подтверждения `QW-LC4-E`

[English version](ADR-092-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-implementation_EN.md)

- **Статус:** принят как ограниченная библиотечная реализация; рабочая точка вызова отсутствует
- **Дата:** 2026-07-31
- **Базовый коммит:** `febfba65d2f200fd2163928643eadd807a6b4d21`

## Контекст

PR №152 зафиксировал контракт вызова материализации и был слит как
`febfba65d2f200fd2163928643eadd807a6b4d21`. Независимая проверка подтвердила
четыре успешные проверки непрерывной интеграции, `124` направленных, `325`
расширенных и `1372` полных теста при `14` предупреждениях. Финальное
подтверждение и остальные рабочие артефакты отсутствовали.

Контракт требует проверять устойчивое состояние до обращения к модулю
материализации. Это необходимо для различения первой операции и восстановления
после неопределённого ответа: уже записанный корректный файл нельзя создавать
повторно.

## Решение

1. Добавить пакет реализации
   `stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-implementation-v1`.
2. Реализовать библиотечный адаптер
   `invoke_final_execution_acknowledgement_materialization`, не добавляя
   производственную точку вызова.
3. Перед любым возможным вызовом классифицировать точный целевой файл:
   - при отсутствии файла разрешить ровно одно делегирование модулю
     материализации;
   - при наличии корректного файла считать операцию завершённой после точной
     проверки байтов, не вызывая модуль материализации;
   - при наличии некорректного файла завершаться закрыто при ошибке.
4. Использовать точный чистый построитель будущей материализации, точный модуль
   материализации и существующий проверяющий модуль сохранённого подтверждения.
   Прямой вызов модуля записи запрещён.
5. Запретить автоматическую и слепую повторную [попытку](../glossary.md#term-attempt).
   Ошибка модуля материализации немедленно возвращается вызывающей стороне; эта
   реализация не повторяет вызов.
6. Допускать явное восстановление только как новую отдельно авторизованную
   операцию с новой проверкой устойчивого состояния.
7. Разрешить запись только в изолированных временных копиях в тестах. Проверка
   пакета, импорт и статические тесты не должны создавать подтверждение.
8. Не создавать файл владения, квитанцию исхода, команду, Docker-вызов и не
   выполнять [локальное вычисление](../glossary.md#term-local-compute).

## Граница

```text
ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_AUTHORING_POST_MERGE_VERIFIED=true
MATERIALIZATION_INVOCATION_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_IMPLEMENTED=true
MATERIALIZATION_INVOKED=false
MATERIALIZER_CALLED=false
WRITER_CALLED=false
AUTOMATIC_RETRY_FORBIDDEN=true
BLIND_RETRY_FORBIDDEN=true
EXPLICIT_RECOVERY_PERMITTED=true
RECOVERY_STATE_PROBE_REQUIRED=true
VALID_EXISTING_TARGET_TREATED_AS_SUCCESS=true
INVALID_EXISTING_TARGET_FAIL_CLOSED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Последствия

После слияния и независимой проверки реализации должен быть открыт отдельный
срез подготовки фактической операторской операции. Наличие адаптера само по себе
не разрешает материализацию и не является подтверждением выполнения.

# ADR-094: реализация операторской операции вызова материализации финального подтверждения `QW-LC4-E`

[English version](ADR-094-stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-implementation_EN.md)

- **Статус:** принят как ограниченная библиотечная реализация; производственная точка вызова отсутствует
- **Дата:** 2026-07-31
- **Базовый коммит:** `5ee6d2346e558be19cfdf79e8a77b0568475bf4c`

## Контекст

PR №154 зафиксировал контракт отдельной операторской операции и был слит как
`5ee6d2346e558be19cfdf79e8a77b0568475bf4c`. Независимая проверка подтвердила
четыре успешные проверки непрерывной интеграции, `162` направленных, `363`
расширенных и `1410` полных тестов при `14` предупреждениях. Операция,
финальное подтверждение и остальные рабочие артефакты отсутствовали.

Контракт требует, чтобы реализация принимала уже сформированный объект операции,
проверяла его фразу, оператора, время и точную связь с будущим вызовом, а затем
обращалась только к существующему адаптеру. Отдельная предварительная проверка
устойчивого состояния запрещена: её выполняет сам адаптер.

## Решение

1. Добавить пакет реализации
   `stage3b-qwake-lc4-e-final-execution-acknowledgement-materialization-invocation-operation-implementation-v1`.
2. Реализовать библиотечную функцию
   `perform_final_execution_acknowledgement_materialization_invocation_operation`.
3. До делегирования проверить полный предварительно сформированный объект операции через
   замороженный контракт ADR-093.
4. Делегировать ровно один раз точному адаптеру
   `invoke_final_execution_acknowledgement_materialization`.
5. Не выполнять отдельную предварительную проверку состояния, не вызывать материализатор или модуль записи
   напрямую и не добавлять производственную точку вызова.
6. Принять оба корректных результата адаптера: новую материализацию и повторное
   использование уже существующего точного подтверждения.
7. Немедленно распространять ошибку адаптера без автоматической или слепой
   повторной [попытки](../glossary.md#term-attempt).
8. Разрешить эффектные тесты только в изолированных временных копиях
   репозитория. Проверка пакета и импорт остаются чистыми.
9. Не создавать файл владения, квитанцию исхода, команду, Docker-вызов и не
   выполнять [локальное вычисление](../glossary.md#term-local-compute).

## Граница

```text
ACKNOWLEDGEMENT_MATERIALIZATION_INVOCATION_OPERATION_AUTHORING_POST_MERGE_VERIFIED=true
MATERIALIZATION_INVOCATION_OPERATION_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_OPERATION_IMPLEMENTED=true
MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false
INVOCATION_ADAPTER_CALLED=false
ADAPTER_CALL_LIMIT=1
STANDALONE_PREPROBE_FORBIDDEN=true
DIRECT_MATERIALIZER_CALL_FORBIDDEN=true
DIRECT_WRITER_CALL_FORBIDDEN=true
AUTOMATIC_RETRY_FORBIDDEN=true
BLIND_RETRY_FORBIDDEN=true
VALID_EXISTING_TARGET_TREATED_AS_SUCCESS=true
INVALID_EXISTING_TARGET_FAIL_CLOSED=true
PRODUCTION_CALLSITE_PRESENT=false
MATERIALIZATION_INVOKED=false
MATERIALIZER_CALLED=false
WRITER_CALLED=false
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
срез подготовки производственной точки вызова. Наличие библиотечной функции не
разрешает и не выполняет материализацию.

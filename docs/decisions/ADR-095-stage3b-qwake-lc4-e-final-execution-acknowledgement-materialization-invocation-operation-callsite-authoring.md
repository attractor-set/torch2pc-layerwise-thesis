# ADR-095: подготовка производственной точки вызова операторской операции материализации подтверждения

- Статус: принят
- Дата: 2026-07-31
- Решение: зафиксировать отдельный проверяемый контракт будущей производственной точки вызова без добавления самой точки вызова и без выполнения операции.

## Контекст

PR №155 реализовал библиотечную операторскую операцию и был независимо проверен после слияния как `23a86cc0769f20b4b7536e64250f3dee062aaa62`. Репозиторий по-прежнему не содержит производственной точки вызова. Нельзя неявно превратить слияние библиотеки в разрешение на создание подтверждения.

## Решение

Будущая точка вызова закрепляется за единственным путём:

```text
scripts/invoke_stage3b_qwake_lc4_final_execution_acknowledgement_materialization_operation.py
```

и единственным делегатом:

```text
torch2pc_thesis.stage3b_qwake_lc4_final_execution_acknowledgement_materialization_invocation_operation_implementation.perform_final_execution_acknowledgement_materialization_invocation_operation
```

Будущий командный интерфейс принимает только явные `--project-root` и `--operation-json`. Файл операции должен содержать канонический предварительно сформированный объект. Стандартный ввод, переменные окружения, интерактивное подтверждение и неявные значения запрещены. Делегат может быть вызван не более одного раза. Отдельная предварительная проверка, прямые вызовы адаптера, материализатора и модуля записи, автоматические и слепые повторы запрещены.

Успех допускается только после проверки результата операции; канонический результат выводится в стандартный вывод. Запись отдельного файла результата запрещена. Реализация точки вызова и последующее [выполнение](../glossary.md#term-execution) операции остаются отдельными срезами.

## Закрытая граница

```text
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_IMPLEMENTED=false
PRODUCTION_CALLSITE_PRESENT=false
MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false
INVOCATION_ADAPTER_CALLED=false
MATERIALIZATION_INVOKED=false
MATERIALIZER_CALLED=false
WRITER_CALLED=false
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
EXECUTION_LEASE_MATERIALIZED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Последствия

После слияния разрешается только отдельный срез реализации точки вызова. Этот ADR не разрешает создавать файл точки вызова, выполнять операцию, материализовать подтверждение, использовать Docker или открывать [локальное вычисление](../glossary.md#term-local-compute).

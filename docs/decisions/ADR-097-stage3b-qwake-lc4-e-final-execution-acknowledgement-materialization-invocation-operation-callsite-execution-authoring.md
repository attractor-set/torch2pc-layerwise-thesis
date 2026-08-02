# ADR-097: подготовка выполнения производственной точки вызова операции материализации подтверждения

- Статус: принят
- Дата: 2026-08-01
- Решение: зафиксировать отдельный проверяемый контракт будущего однократного [выполнения](../glossary.md#term-execution) уже реализованной производственной точки вызова без авторизации и без выполнения.

## Контекст

PR №163 реализовал производственную точку вызова и был независимо проверен после слияния как `78129528d05e8268b4e40fdf708fd9d2c8e3ab29`. Наличие исполняемого файла не разрешает его [запуск](../glossary.md#term-run). Текущая ветка не содержит авторизации выполнения, канонического файла операции или разрешения на создание подтверждения.

## Решение

Будущее [выполнение](../glossary.md#term-execution) связывается с точным файлом:

```text
scripts/invoke_stage3b_qwake_lc4_final_execution_acknowledgement_materialization_operation.py
```

и отдельной фразой действия:

```text
EXECUTE_QWAKE_LC4_FINAL_EXECUTION_ACKNOWLEDGEMENT_MATERIALIZATION_OPERATION_CALLSITE
```

Будущая авторизация должна отдельно зафиксировать идентичность оператора, время, точный SHA-256 канонического `operation.json` и коммит выполнения. Файл операции и авторизация остаются отсутствующими на этом этапе. Авторизация должна быть слита и независимо проверена до попытки запуска.

Перед единственной попыткой требуется повторно проверить точный коммит, Torch2PC, чистоту рабочего дерева и индекса, SHA-256 точки вызова и файла операции, а также отсутствие подтверждения, обоих файлов владения, устойчивого исхода, каталога результата и `staging`. Команда должна выполняться без оболочки, из точного корня проекта, с явными `--project-root` и `--operation-json`. Автоматический или слепой повтор запрещён.

Успех требует нулевого кода завершения и единственного канонического объекта в стандартном выводе. Вывод до подтверждённого успеха и отдельный файл результата запрещены.

## Закрытая граница

```text
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_CONTRACT_AUTHORED=true
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_AUTHORIZED=false
PRODUCTION_CALLSITE_PRESENT=true
PRODUCTION_CALLSITE_EXECUTED=false
MATERIALIZATION_INVOCATION_OPERATION_CALLSITE_EXECUTION_PERFORMED=false
MATERIALIZATION_INVOCATION_OPERATION_PERFORMED=false
INVOCATION_ADAPTER_CALLED=false
MATERIALIZER_CALLED=false
WRITER_CALLED=false
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Последствия

После слияния разрешается только отдельный срез авторизации выполнения. Этот ADR не разрешает создавать `operation.json`, запускать точку вызова, выполнять операцию, создавать подтверждение, использовать Docker или открывать [локальное вычисление](../glossary.md#term-local-compute).

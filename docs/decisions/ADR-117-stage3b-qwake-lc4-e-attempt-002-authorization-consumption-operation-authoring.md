# ADR-117: подготовка операции потребления авторизации попытки 002

- Статус: принято
- Дата: 2026-08-04
- Срез: `QW-LC4-E-attempt-002-authorization-consumption-operation-authoring`

## Контекст

Шестой коммит PR №179 и отдельная [фиксация](../glossary.md#term-freeze)
области независимо проверены. Одноразовая авторизация
[попытки](../glossary.md#term-attempt) 002 остаётся эффективной и
непотреблённой. Владение, результат и
[выполнение](../glossary.md#term-execution) не начаты.

Следующий переход обязан отделить описание одноразовой операции от её
производственного вызова. Наличие модуля не должно само по себе создавать
процесс, контейнер, каталог вывода или терминальные
[доказательные материалы](../glossary.md#term-evidence).

## Решение

Создать отдельную свободную от эффектов при импорте операцию
`execute_attempt_002_authorization_consumption_operation_once`.

Операция:

1. принимает явно сформированный допуск после коммита;
2. требует точного коммита реализации, чистого рабочего дерева и точной
   идентичности Torch2PC;
3. требует эффективную и непотреблённую авторизацию при отсутствии всех
   артефактов попытки 002;
4. создаёт каноническое заявление права в памяти;
5. вызывает ровно один внедрённый делегированный переход;
6. запрещает автоматический повтор после ошибки или неизвестного результата.

Модуль не импортирует `subprocess`, Docker-клиент или код среды выполнения.
Производственная точка вызова, конкретное средство запуска процессов и внешний
[запуск](../glossary.md#term-run) не создаются.

## Проверяемая граница

Модуль операции, проверяющий модуль, тесты и трёхфайловый пакет созданы.
Тесты выполняют только синтетический делегированный переход в изолированных
временных репозиториях. Они не используют рабочее дерево проекта как цель
эффекта.

Пакет авторизации и терминальные
[доказательные материалы](../glossary.md#term-evidence) попытки 001 остаются
неизменными.

```text
ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_SCOPE_FREEZE_POST_COMMIT_VERIFIED=true
ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_AUTHORING_ADMISSIBLE=true
ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_AUTHORED=true
ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_POST_COMMIT_VERIFIED=false
ATTEMPT_002_AUTHORIZATION_CONSUMPTION_OPERATION_INVOKED=false
PRODUCTION_CALLSITE_PRESENT=false
HOST_PROCESS_SPAWNER_PRESENT=false
ATTEMPT_002_AUTHORIZATION_CONSUMED=false
ATTEMPT_002_ATTEMPT_STARTED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
AUTHORIZATION_CONSUMPTION_PERMITTED=false
DO_NOT_MERGE_YET=true
```

## Последствия

Седьмой коммит должен содержать только замороженные семнадцать путей. После
коммита требуется отдельный аудит только для чтения. До его успешного завершения
потребление авторизации, производственный вызов операции и слияние PR №179
остаются запрещёнными.

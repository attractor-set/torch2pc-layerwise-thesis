# ADR-108: подготовка атомарного перехода потребления разрешения

## Статус

Принято для отдельного среза подготовки, требующего слияния. Эксплуатационный эффект закрыт.

## Контекст

[ADR-107](ADR-107-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-scope-freeze.md) зафиксировал единственную точку устойчивой фиксации: создание без замены жёсткой ссылки на точные, предварительно синхронизированные байты постоянной аренды исполнения v2. После слияния PR №175 и независимой проверки зафиксированная область допускает подготовку реализации, но не сам атомарный эффект.

## Решение

Создать отдельный пакет `stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-v1`, содержащий:

- модуль атомарного перехода;
- самостоятельный проверяющий модуль;
- тесты, причём все тесты с файловым эффектом выполняются только во временных копиях репозитория;
- каноническую неизменяемую запись `transition.json`;
- реестры `source-SHA256SUMS` и `SHA256SUMS`.

Точка входа, способная создать эффект, называется `execute_final_engineering_invocation_atomic_transition_once`. Само её наличие не разрешает вызов. Проверяющий модуль подготовки не вызывает эту точку входа и не импортирует `invoke_lease_bound_host_runtime`.

## Реализованный протокол фиксации

Будущий вызов обязан:

1. получить независимо установленное подтверждение после слияния для точного коммита реализации;
2. проверить новое разрешение, подготовленную попытку, область ADR-107 и личность оператора;
3. проверить разные обязательные значения фразы действия разрешения и подтверждения аренды v2;
4. построить существующую точную схему постоянной аренды v2, где `execution_commit` равен проверенному коммиту слияния реализации;
5. использовать существующий проверенный механизм записи с `O_CREAT|O_EXCL`, синхронизацией файла, созданием жёсткой ссылки без замены, синхронизацией каталога, проверкой точных байтов и режима `0600`;
6. выводить `authorization_consumed=true`, `attempt_started=true` и `atomic_action_committed=true` только из точных байтов конечной аренды v2.

Вызов среды исполнения расположен после атомарной фиксации и вне данной точки входа. Модуль не импортирует точку входа среды исполнения.

## Закрытые при ошибках состояния

- Ошибка до точки фиксации оставляет разрешение непотреблённым, попытку неначатой, а конечную аренду отсутствующей.
- Уже существующая точная аренда означает завершённую фиксацию и запрет повтора.
- Неэквивалентный, символический, частичный или неоднозначный конечный объект означает `unknown_fail_closed`; [запуск](../glossary.md#term-run) среды исполнения и повтор запрещены.
- Ошибка после появления точной аренды также означает завершённую фиксацию и запрет повтора.

## Граница подготовки

```text
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_FROZEN=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_FREEZE_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_AUTHORING_ADMISSIBLE=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_AUTHORED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_FREEZE_ADMISSIBLE=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_COMMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_STARTED=false
INVOCATION_COMMAND_MATERIALIZED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
QW5_TRANSITION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
```

## Последствия

После слияния ADR-108 и независимой проверки допустима только отдельная неисполняющая фиксация области эксплуатационной операции атомарного перехода. Ни подготовка ADR-108, ни её слияние сами по себе не потребляют разрешение и не создают аренду v2.

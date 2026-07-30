# ADR-082: восстановление идентичности операции рабочей среды `QW-LC4-E`

[English version](ADR-082-stage3b-qwake-lc4-e-runtime-operation-identity-repair_EN.md)

- **Статус:** принят как авторинг исправления идентичности; [выполнение](../glossary.md#term-execution) заблокировано
- **Дата:** 29 июля 2026 года
- **Базовый коммит:** `97dacb207aa201f1fd2f43c66ae34b1adced32bb`

## Контекст

После однострочной Ruff-коррекции `UP038` фактический модуль ADR-081 перестал
соответствовать SHA-256, записанному в историческом ADR. PR №142 корректно
слил исправленное дерево исходного кода, но исходный двухфайловый пакет
`runtime-operation-v1` связывал только `operation.json` и не мог обнаружить расхождение
самого исполняемого модуля.

Исторический ADR-081 и пакет `runtime-operation-v1` нельзя переписывать. Нужна
отдельная, не ретроактивная запись исправления, которая связывает фактический
модуль, проверяющую программу, тесты и обе версии ADR с точным коммитом слияния PR №142.

## Решение

1. Сохранить ADR-081 и его двухфайловый замороженный пакет без изменений как
   исторический артефакт авторинга.
2. Добавить пакет
   `stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation-identity-repair-v1`
   из `repair.json`, `source-SHA256SUMS` и `SHA256SUMS`.
3. Связать реестр исходных файлов с исправленным модулем операции рабочей
   среды, прежними проверяющей программой и тестом, ADR-081 RU/EN, ADR-082
   RU/EN и собственными модулем, проверяющей программой и тестом исправления.
4. Сделать `verify_engineering_invocation_runtime_operation` зависимым от
   успешной проверки восстановления идентичности без эффектов ровно один раз.
5. Отклонять старый SHA модуля как действующую идентичность и сохранять его
   только как явно помеченную историческую ошибку.
6. Не открывать выполнение: полная квитанция проверки, слияние исправления,
   постоянный файл владения v2 и устойчивая квитанция отрицательного исхода
   хоста остаются отдельными обязательными барьерами.

## Идентичности

```text
runtime_operation_head_commit=423684f3e8eaad1858161503d63d514a5eeb9e5e
runtime_operation_merge_commit=97dacb207aa201f1fd2f43c66ae34b1adced32bb
runtime_operation_merged_at_utc=2026-07-30T00:31:26Z
historical_runtime_operation_sha256=sha256:0332428014f7f8385c789ba7e7c55d6c2ec03b020e3f83df9ac9714483bb6bf8
stale_module_sha256=sha256:eb337b1f9cd1c95570d7ec22160886a43efe2531c9c5131b7ac29a84123115a4
corrected_module_sha256=sha256:da08c66e78340c067e391a28f326f0d9bb7465d4a56073deac458a764ae6b30d
runtime_operation_verifier_sha256=sha256:78fe6cee7af7f3d652a5b16c1d095540a47dd12177d253c1f8d37da0c812fbc4
runtime_operation_test_sha256=sha256:76ede6b6f004d9ddab0bca2fb8891bf3d69d7355665e8fb729f2cf3c0c651ee5
historical_adr_ru_sha256=sha256:eb16141e0fe86f80075c6753512f3b4bda5a5244598b81874af4d4eed42946da
historical_adr_en_sha256=sha256:b4d17e5d2d9c11c2ca75876331eca845637f3cb7f1cc00ea8897465cbe959370
identity_repair_sha256=sha256:ff6d22e98257bb55774abf8ad2418a60c759981049994720ae814e9ff6ccc4c6
```

## Границы

```text
HISTORICAL_RUNTIME_OPERATION_PACKAGE_PRESERVED=true
CORRECTED_MODULE_IDENTITY_FROZEN=true
RUNTIME_OPERATION_SELF_IDENTITY_VERIFIED=true
CORRECTED_FULL_VALIDATION_RECEIPT_PRESENT=false
RUNTIME_OPERATION_IDENTITY_REPAIR_MERGED=false
LATEST_AUTHORIZATION_BOUND_IN_PERSISTENT_LEASE=false
DURABLE_NEGATIVE_HOST_OUTCOME_DEFINED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Последствия

Исправленная идентичность исходного кода теперь проверяется по фактическому
дереву, а изменение модуля операции рабочей среды, проверяющей программы,
тестов или связанных ADR приводит к закрытию при ошибке. Следующий допустимый
срез после коммита, PR, слияния и проверки после слияния — постоянная
доказательная цепочка v2. Запрос выполнения и одноразовый
[запуск](../glossary.md#term-run) до этого недопустимы.

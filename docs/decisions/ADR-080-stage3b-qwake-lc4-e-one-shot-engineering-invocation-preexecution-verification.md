# ADR-080: контракт проверки перед выполнением одноразового инженерного вызова `QW-LC4-E`

[English version](ADR-080-stage3b-qwake-lc4-e-one-shot-engineering-invocation-preexecution-verification_EN.md)

- **Статус:** принят как авторинг контракта; динамическая проверка и [выполнение](../glossary.md#term-execution) не начаты
- **Дата:** 29 июля 2026 года
- **Базовый коммит:** `49c4b97e93b47cefbf35576736927ece02c9402b`

## Контекст

PR №140 завершил слияние авторизации одного будущего инженерного вызова. Эта
авторизация требует, чтобы проверка текущего образа, ресурсов хоста,
канонического вектора аргументов и закрытой границы эффектов происходила в том
же процессе, который затем создаёт единственный дочерний процесс. Отдельная
подготовительная проверка не может считаться динамической проверкой рабочей
среды: она нарушила бы непрерывность проверки и запуска и увеличила бы число
проверок образа и материализаций команды.

Перед фактическим [запуском](../glossary.md#term-run) требуется заморозить точный
контракт этой непрерывности и закрытую при ошибке проверяющую программу, которая
подтверждает неизменность уже реализованного хостового исполнителя, но сама не
вызывает его.

## Решение

Материализовать двухфайловый пакет
`stage3b-qwake-lc4-e-one-shot-engineering-invocation-preexecution-verification-v1`,
чистый модуль, консольную проверку и отрицательные тесты. Контракт:

1. связывает коммит слияния PR №140, головной коммит авторизации, его родителя и
   полный пакет `execution-authorization-v1`;
2. повторно связывает точный контракт и реализацию хостового исполнителя,
   неизменяемый образ, Torch2PC, каталог результата и путь файла владения;
3. требует прямой однократный вызов `invoke_one_shot_host_runtime` в будущей
   атомарной операции, без промежуточной отдельной динамической проверки;
4. фиксирует 13 точных ключей ресурсов хоста, две проверки образа, две
   материализации канонического `argv`, равенство обеих пар и не более одного
   `Popen` без оболочки;
5. требует непотреблённую авторизацию и отсутствие файла владения, результата и
   `staging` перед созданием дочернего процесса;
6. запрещает запись команды и хостовых журналов, запись файла владения хостом и
   автоматический повтор после создания процесса;
7. подтверждает только статический контракт и сохраняет
   `PREEXECUTION_IDENTITY_VERIFIED=false` до будущего вызова в текущей рабочей
   среде.

Проверяющая программа вызывает только чистые проверки зафиксированных пакетов и
реализации. Она не выполняет `docker image inspect`, не материализует команду,
не вызывает `Popen`, не создаёт файл владения и не формирует
[доказательные материалы](../glossary.md#term-evidence).

## Идентичности

```text
preexecution_base_commit=49c4b97e93b47cefbf35576736927ece02c9402b
authorization_head_commit=9b7074cbb602fff77ad6770ea4978d3bdc73003b
authorization_parent_commit=b0f6729e8fd1cb1aa172eef488dc56e36b335173
authorization_merged_at_utc=2026-07-29T21:46:26Z
execution_authorization_sha256=sha256:ff136538faee0d7952dc444e521d7ec760c7d54cd38406cb9b19ff1e00d9437b
preexecution_verification_sha256=sha256:833371b427a5c8a6e602d675711b85b2edc68441b9e5be191321a2911bce6128
verification_file_sha256=sha256:a0f19309fc7bb2abe47f300a793423e8c764d6330220b4d4e8db3724c01df9f1
package_registry_sha256=sha256:cee3dda10e7d1249ae0a6fb56173a491dd2b87adb916b42b88a10e9e9c801028
module_sha256=sha256:cae8721fb3278a3fbfeda8db366e864b75dd576fae90cfafe4c62301205dd2f6
verifier_sha256=sha256:bf052424ecfabe85741ce4ddf13112db5797c2bc666c6b026bb4dd9bac55e4cd
test_sha256=sha256:18386e940984402b5e54c66c9a93cbf692a73be8e2ee4ee6c858a9a314cd1752
```

## Границы

```text
INVOCATION_OPERATION_COMPLETE=true
EXECUTION_AUTHORIZATION_COMPLETE=true
PREEXECUTION_VERIFICATION_RECORD_PRESENT=true
PREEXECUTION_VERIFIER_IMPLEMENTED=true
PREEXECUTION_STATIC_CONTRACT_VERIFIED=true
PREEXECUTION_VERIFICATION_SLICE_OPEN=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_EXECUTION_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_OPEN=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Последствия

После фиксации и слияния этого контракта может быть открыта только отдельная
атомарная операция фактического вызова. Она обязана вызвать точный хостовый
исполнитель один раз; его две проверки образа и две материализации команды
должны происходить в том же процессе непосредственно перед единственным
созданием дочернего процесса. Любое расхождение завершает операцию закрыто и не
разрешает обход или автоматический повтор.

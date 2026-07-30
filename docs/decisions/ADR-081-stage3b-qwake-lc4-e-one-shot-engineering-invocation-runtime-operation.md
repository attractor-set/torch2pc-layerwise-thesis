# ADR-081: ограниченная операция одноразового инженерного вызова `QW-LC4-E`

[English version](ADR-081-stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation_EN.md)

- **Статус:** принят как авторинг операции; динамическая проверка и [выполнение](../glossary.md#term-execution) не начаты
- **Дата:** 29 июля 2026 года
- **Базовый коммит:** `494e6a0b2f10c26b49c90fbb84c23565699a4064`

## Контекст

PR №141 завершил слияние статического контракта проверки перед выполнением.
Следующий срез должен определить единственную точку входа, которая после
отдельного подтверждения слияния сможет делегировать один вызов уже
зафиксированному хостовому исполнителю. Новая точка входа не должна повторять
проверку образа, материализацию команды или создание дочернего процесса: эти
действия уже объединены в `invoke_one_shot_host_runtime` и должны оставаться в
одном непрерывном процессе.

При этом наличие исполнимой функции не является разрешением на [запуск](../glossary.md#term-run). Ветка
авторинга должна сохранять явный закрытый допуск, пустую границу эффектов и
`PREEXECUTION_IDENTITY_VERIFIED=false`.

## Решение

Материализовать двухфайловый пакет
`stage3b-qwake-lc4-e-one-shot-engineering-invocation-runtime-operation-v1`,
чистый машиночитаемый контракт, проверяющую программу, отрицательные тесты и
ограниченную точку входа
`execute_one_shot_engineering_invocation_runtime_operation`.

Контракт:

1. связывает коммит слияния PR №141, головной и родительский коммиты контракта
   проверки перед выполнением и полный пакет `preexecution-verification-v1`;
2. повторно связывает точный хостовый исполнитель, одноразовую авторизацию,
   неизменяемый образ, Torch2PC, каталог результата и путь файла владения;
3. требует отдельное точное подтверждение операции и буквальное
   `runtime_execution_permitted=true`;
4. требует время требования в `UTC` после слияния PR №141, точный набор из 13
   ключей ресурсов хоста и прежнее подтверждение одноразовой авторизации;
5. делегирует ровно один вызов `invoke_one_shot_host_runtime`, внутри которого
   выполняются две проверки образа, две материализации канонического `argv` и
   не более одного `Popen`;
6. запрещает прямые вызовы проверки образа, материализации команды, `Popen`,
   захвата файла владения и контейнерной точки входа из нового модуля;
7. требует закрытую границу эффектов непосредственно перед делегированием и
   запрещает автоматический повтор;
8. не вызывает исполняющую точку входа из проверяющей программы или тестов с
   реальными адаптерами.

Точка входа проверяет статический пакет, подтверждения, разрешение, время,
ключи ресурсов и отсутствие результата, файла владения и временного каталога.
Только после этого она может один раз делегировать управление существующему
хостовому исполнителю. В состоянии авторинга разрешение остаётся закрытым.

## Идентичности

```text
runtime_operation_base_commit=494e6a0b2f10c26b49c90fbb84c23565699a4064
preexecution_head_commit=bb888b900401894441f37fdbbe21c1e25c288366
preexecution_parent_commit=49c4b97e93b47cefbf35576736927ece02c9402b
preexecution_merged_at_utc=2026-07-29T23:21:31Z
preexecution_verification_sha256=sha256:833371b427a5c8a6e602d675711b85b2edc68441b9e5be191321a2911bce6128
runtime_operation_sha256=sha256:0332428014f7f8385c789ba7e7c55d6c2ec03b020e3f83df9ac9714483bb6bf8
operation_file_sha256=sha256:ba9b514980bf5f8629cc6a140a0b95114689020a4cffb8bf3ce4a58fade10247
package_registry_sha256=sha256:d213e051076a1990b268abfd28dcb4d98c699865fc19039ebfece50761f5e46c
module_sha256=sha256:eb337b1f9cd1c95570d7ec22160886a43efe2531c9c5131b7ac29a84123115a4
verifier_sha256=sha256:78fe6cee7af7f3d652a5b16c1d095540a47dd12177d253c1f8d37da0c812fbc4
test_sha256=sha256:76ede6b6f004d9ddab0bca2fb8891bf3d69d7355665e8fb729f2cf3c0c651ee5
```

## Границы

```text
EXECUTION_AUTHORIZATION_COMPLETE=true
PREEXECUTION_VERIFICATION_COMPLETE=true
PREEXECUTION_STATIC_CONTRACT_VERIFIED=true
RUNTIME_OPERATION_RECORD_PRESENT=true
RUNTIME_OPERATION_EXECUTOR_ENTRYPOINT_IMPLEMENTED=true
RUNTIME_OPERATION_STATIC_CONTRACT_VERIFIED=true
ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_RUNTIME_OPERATION_OPEN=true
PREEXECUTION_IDENTITY_VERIFIED=false
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

После фиксации и слияния этого среза отдельная операция выполнения может
сформировать точные значения ресурсов и времени и вызвать новую точку входа с
явным разрешением. До такой отдельной операции никакая динамическая проверка,
материализация команды, запись файла владения или [локальное вычисление](../glossary.md#term-local-compute) не
разрешены. Любое расхождение завершает вызов закрыто до делегирования, а после
создания дочернего процесса автоматический повтор запрещён существующим
хостовым исполнителем.

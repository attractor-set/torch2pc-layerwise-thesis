# ADR-076: фиксация состояния репозитория одноразового хостового исполнителя `QW-LC4-E`

[English version](ADR-076-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-repository-freeze_EN.md)

- **Статус:** принято
- **Дата:** 29 июля 2026 года
- **Область:** `QW-LC4-E`, репозиторная граница перед одноразовым инженерным вызовом

## Контекст

Реализация `stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-implementation-v1`
слита через PR №136 в `main` `da51c8d858c541372525125640db99062041fc20`.
Проверка после слияния зафиксировала два точных родителя, совпадение дерева с
головным коммитом `181abda36465d3a91db5970e684938266200a798`, 16-файловый
состав, две успешные CI-проверки, 139 целевых и 1186 полных тестов.

Перед отдельной операторской операцией требуется [фиксация целостности](../glossary.md#term-integrity-sealing),
которая связывает реализацию исполнителя с конкретным состоянием `main`, но не
предоставляет веточный допуск [выполнения](../glossary.md#term-execution).

## Решение

1. Материализовать двухфайловую квитанцию
   `stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-repository-freeze-v1`.
2. Связать её с PR №136, точным коммитом слияния, двумя родителями и временем
   слияния.
3. Зафиксировать семантический хэш реализации, контракт исполнителя, хэши
   модуля, проверяющей программы, теста, `implementation.json`, его реестра и
   точную ревизию Torch2PC.
4. Записать результаты CI и локальной проверки как идентичность инженерного
   среза, а не как научный результат.
5. Сохранить предшествующие [доказательные материалы](../glossary.md#term-evidence)
   неизменными и не выполнять проверку образа или `docker run` в этом срезе.
6. До слияния и независимой повторной проверки квитанции оставить одноразовый
   инженерный вызов, файл владения, потребление разрешения, результаты и
   публикацию закрытыми.

## Проверяемая граница

```text
qwake_adr=ADR-076-stage3b-qwake-lc4-e-one-shot-host-runtime-invoker-repository-freeze
qwake_host_runtime_invoker_repository_main_commit=da51c8d858c541372525125640db99062041fc20
qwake_host_runtime_invoker_implementation_head=181abda36465d3a91db5970e684938266200a798
qwake_host_runtime_invoker_repository_freeze_materialized=true
qwake_host_runtime_invoker_repository_freeze_complete=false
qwake_next_slice=QW-LC4-E-one-shot-host-runtime-invoker-repository-freeze-merge
qwake_post_merge_next_slice=QW-LC4-E-one-shot-engineering-invocation
HOST_RUNTIME_INVOKER_IMPLEMENTATION_PRESENT=true
HOST_RUNTIME_INVOKER_PRESENT=true
HOST_RUNTIME_INVOKER_EXECUTABLE=true
HOST_DOCKER_RUN_IMPLEMENTED=true
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
IMAGE_INSPECTION_PERFORMED=false
DOCKER_RUN_PERFORMED=false
RUNTIME_RERUN_PERFORMED=false
FILES_STAGED=false
```

## Последствия

Только слияние этой квитанции и отдельная проверка после слияния могут завершить
репозиторную заморозку и разрешить подготовку атомарной одноразовой операторской
операции. Сама ADR-076 не запускает исполнитель и не потребляет существующее
разрешение.

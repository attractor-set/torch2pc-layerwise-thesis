# ADR-072: проектирование хостовой обёртки одноразового вызова `QW-LC4-E`

[English version](ADR-072-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-authoring_EN.md)

- **Статус:** принят как срез проектирования; хостовый исполнитель отсутствует
- **Дата:** 29 июля 2026 года
- **Срез:** `QW-LC4-E-one-shot-invocation-wrapper-authoring`

## Контекст

Разрешение одного будущего инженерного вызова слито через PR №132 в `main`
коммитом `8337d9ad0ac21a69a577ab74a73d05d69f8fa7a1` и независимо проверено.
Оно разрешает будущий захват файла владения и [выполнение](../glossary.md#term-execution) точного неизменяемого
образа, но сохраняет веточный барьер
`branch_runtime_execution_permitted=false`.

Внутри образа уже существует точка входа, которая при явном вызове проверяет
`execution-freeze-v1`, захватывает файл владения и выполняет синтетическую
матрицу. Поэтому следующий слой нельзя смешивать с запуском: сначала требуется
чисто описать хостовую обёртку, допустимые монтирования, среду и обязательные
проверки образа.

## Решение

1. Добавить чистый модуль
   `stage3b_qwake_lc4_invocation_wrapper.py`, который повторно проверяет точный
   пакет разрешения и строит только канонический контракт будущего вызова.
2. Привязать контракт к коммитам слияния и вершины PR №132, SHA-256 разрешения, точному
   `image repo digest`, исходному коммиту образа, Torch2PC и внутренней точке
   входа.
3. Разрешить только три будущих монтирования каталогов:
   - `experiments/frozen -> /workspace/experiments/frozen` только для чтения;
   - `external/Torch2PC -> /workspace/external/Torch2PC` только для чтения;
   - `results -> /workspace/results` для чтения и записи.
4. Запретить монтирование исходного дерева проекта и любого набора данных.
5. Будущая реализация обязана использовать образ по `repo digest`, проверить
   его идентификатор и метку исходного коммита до запуска, отключить сеть,
   использовать корневую файловую систему только для чтения,
   `no-new-privileges`, сброс возможностей и запрет привилегированного режима.
6. Для совместимости с зафиксированной точкой входа при корневой файловой
   системе только для чтения обязательна отдельная временная файловая система
   `/tmp`; её размер задаётся явным входом `TMPFS_SIZE`.
7. Зафиксированы будущие подключения `/dev/kfd` и `/dev/dri`, пользователь
   `HOST_UID:HOST_GID`, дополнительные группы `VIDEO_GID` и `RENDER_GID`,
   процессорный набор, память, разделяемая память и ограничения потоков.
8. Зафиксирован точный шаблон команды внутренней точки входа с единственным
   динамическим значением `{CLAIMED_AT_UTC}`. Значения ресурсов хоста должны
   проверяться до материализации команды; текущий срез их не читает.
9. Вызов, захват и выполнение должны оставаться одним процессом; после захвата
   повтор запрещён.
10. Проверяющая программа может только построить, сериализовать во временный
   каталог и повторно загрузить контракт. Она не импортирует среду тензорных вычислений,
   не вызывает Docker и не создаёт репозиторных эффектов.

## Машиночитаемый контракт

```text
contract_id=stage3b-qwake-lc4-e-one-shot-host-invocation-wrapper-contract-v1
contract_sha256=sha256:4c4cb163e8c2a33b0563cc3b9cb873a87acf8ea75bb3e807d157d51c5a4dd29b
authorization_merge_commit=8337d9ad0ac21a69a577ab74a73d05d69f8fa7a1
authorization_head_commit=ca6363c11218575d567c5dd6cbe8818d10a86d41
image_repo_digest=torch2pc-layerwise-thesis@sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d
```

## Границы

```text
INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
INVOCATION_WRAPPER_AUTHORING_BRANCH_OPEN=true
INVOCATION_WRAPPER_CONTRACT_PRESENT=true
CONTAINER_COMMAND_TEMPLATE_PRESENT=true
GPU_DEVICE_BINDING_COUNT=2
TMPFS_REQUIRED=true
TMPFS_TARGET=/tmp
HOST_RUNTIME_INVOKER_PRESENT=false
IMAGE_INSPECTION_IMPLEMENTED=false
INVOCATION_COMMAND_MATERIALIZED=false
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
```

## Последствия

После коммита, слияния и независимой проверки отдельный срез может реализовать
хостовый исполнитель. Даже наличие такого кода не должно открывать выполнение:
фактическая одноразовая команда допускается только после отдельной проверки
точного коммита реализации, локального образа и всех входов ресурсов.

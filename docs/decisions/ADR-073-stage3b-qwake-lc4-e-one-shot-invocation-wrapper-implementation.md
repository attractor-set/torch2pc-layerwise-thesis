# ADR-073: реализация хостовой обёртки одноразового вызова `QW-LC4-E`

[English version](ADR-073-stage3b-qwake-lc4-e-one-shot-invocation-wrapper-implementation_EN.md)

- **Статус:** принята как реализация без хостового исполнителя
- **Дата:** 29 июля 2026 года
- **Срез:** `QW-LC4-E-one-shot-invocation-wrapper-implementation`

## Контекст

PR №133 с чистым контрактом обёртки слит в `main`
`7cc17c6b36cb5115e63a2b64e4bff90a525b2465` и независимо проверен. Контракт
требует перед будущим вызовом проверить точный локальный образ и построить
каноническую команду, но не разрешает [выполнение](../glossary.md#term-execution)
на ветке реализации.

Локальный образ уже зафиксирован как
`torch2pc-layerwise-thesis@sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d`.
Его нормализованная запись проверки входит в неизменяемый пакет
`execution-freeze-v1`. Поэтому реализация должна сравнивать текущее наблюдение
Docker с этой записью, а не доверять тегу или свободно заданной строке образа.

## Решение

1. Добавить отдельный модуль
   `stage3b_qwake_lc4_invocation_wrapper_implementation.py`.
2. Разрешить модулю только одну наблюдательную внешнюю операцию:
   `docker image inspect` для точного `image repo digest`.
3. Запретить оболочку командной строки, `docker pull`, [запуск](../glossary.md#term-run) контейнера,
   импорт тензорной [среды выполнения](../glossary.md#term-runtime), захват файла
   владения и запись результатов.
4. Нормализовать и сверять с замороженной записью:
   - `image ID` и `RepoDigests`;
   - обязательный тег;
   - архитектуру, ОС, время создания, размер и все слои `RootFS`;
   - метки `org.opencontainers.image.revision` и `io.torch2pc.base-image`;
   - `SOURCE_GIT_COMMIT` внутри образа;
   - точную точку входа образа и рабочий каталог.
5. Принимать ровно 13 входов ресурсов хоста. Идентификаторы, список GPU,
   набор CPU, размеры и количества потоков должны иметь каноническое
   представление; лишние или неоднозначные значения закрывают проверку.
6. Материализовать будущий `docker run` только как неизменяемый кортеж `argv`
   в памяти. Он обязан содержать `--pull=never`, отключённую сеть, корневую
   файловую систему только для чтения, `no-new-privileges`, сброс всех
   возможностей, два устройства и ровно три монтирования из ADR-072.
7. Не сохранять команду в репозитории и не предоставлять функцию, способную её
   выполнить. Единственный вызов `subprocess.run` принадлежит проверке образа.
8. Сохранять файл владения, разрешение, [доказательные материалы](../glossary.md#term-evidence),
   [набор данных](../glossary.md#term-dataset) и публикацию неизменёнными.

## Машиночитаемая граница

```text
implementation_id=stage3b-qwake-lc4-e-one-shot-host-invocation-wrapper-implementation-v1
implementation_base_commit=7cc17c6b36cb5115e63a2b64e4bff90a525b2465
wrapper_contract_sha256=sha256:4c4cb163e8c2a33b0563cc3b9cb873a87acf8ea75bb3e807d157d51c5a4dd29b
frozen_image_inspection_sha256=sha256:d771d93b4b3c38599fee9fbf90971bc8d00d9cd7da4cbe90cef67c84d761d675
```

```text
IMAGE_INSPECTION_IMPLEMENTED=true
INVOCATION_COMMAND_MATERIALIZED=true
INVOCATION_COMMAND_PERSISTED=false
HOST_RUNTIME_INVOKER_PRESENT=false
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

После слияния и отдельной проверки репозиторий будет содержать проверку образа
и детерминированный построитель команды. Наличие этих функций не открывает
[выполнение](../glossary.md#term-execution). Перед фактическим вызовом требуется
отдельная фиксация реализации, проверка реальных входов ресурсов и отдельный
атомарный шаг, который одновременно использует одноразовое разрешение, создаёт
файл владения и вызывает уже замороженную точку входа без повтора.

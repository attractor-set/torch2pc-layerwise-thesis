# ADR-063: фиксация рабочей среды `QW-LC4-F`

[English version](ADR-063-stage3b-qwake-lc4-f-runtime-freeze_EN.md)

- Статус: принято
- Дата: 27 июля 2026 года

## Контекст

[Авторинг `QW-LC4-F`](ADR-062-stage3b-qwake-lc4-f-runtime-freeze-authoring.md)
зафиксировал последовательность: исходный код и запрос, затем образ,
предварительная проверка, статическая квитанция и одноразовое разрешение.
[Выполнение](../glossary.md#term-execution) механизма при этом не открывалось.

Из точного коммита
`51fc7537fdcb395145fc4c5a38b8918b018fe892` построен образ
`sha256:a31cf96e20ab45ce29fe18b68eb805bd048a02f1f8107cf680d1c174ea363929`.
Проверки CPU/ROCm и канонический валидатор разрешения прошли.
[Локальное вычисление](../glossary.md#term-local-compute) не производилось.

## Решение

1. Зафиксировать десятифайловый пакет
   `stage3b-qwake-lc4-f-runtime-freeze-v1`.
2. Связать его с точными идентичностями исходного кода, Torch2PC, образа,
   запроса, реализации `QW-LC4-I`, контракта `QW-LC3`, предварительной проверки,
   статической квитанции и разрешения.
3. Считать разрешение перспективным и ограниченным одной
   [попыткой](../glossary.md#term-attempt): 14 ячеек рабочей среды,
   168 сопоставленных ячеек и 28 резервных зондов.
4. Не считать разрешение исполнением. Пакет одновременно фиксирует
   `runtime_execution_permitted=true`,
   `runtime_execution_performed=false` и отсутствие
   [доказательных материалов](../glossary.md#term-evidence).
5. Оставить `QW-LC4-F` незавершённым до слияния и независимой проверки
   после слияния.
6. Только успешная проверка после слияния может разрешить отдельный срез
   `QW-LC4-E`. Научное исполнение, доступ к
   [набору данных](../glossary.md#term-dataset), публикация и активация политики
   остаются закрытыми.

## Точные идентичности

```text
source_commit=51fc7537fdcb395145fc4c5a38b8918b018fe892
torch2pc_commit=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
image_digest=sha256:a31cf96e20ab45ce29fe18b68eb805bd048a02f1f8107cf680d1c174ea363929
preflight_sha256=sha256:3a8d7817338f3b93396270ea8e1b1b2fbda768dbd5461a18f97520948a53a9e6
authorization_sha256=sha256:d11b662a5c5eeada5333e69c6fddf2e50726c01b4d8c78a556a68167dbdd301e
manifest_file_sha256=sha256:4840d39d7c19133aeb3f20c572c17677f84ad2f82697dc4ad75dcccb99bb52c1
freeze_registry_sha256=sha256:8f8a0dfaaff934ac3c8f654e7e65d9460168755532547dcf924e51c6451aeb6d
source_registry_sha256=sha256:f80fe750b26afda55be19f9f2322baade6c7f07b11ee0d0a431ad88c1136d7b0
```

`manifest.json` не содержит собственного хэша. Его идентичностью является
SHA-256 всего файла.

## Происхождение журналов

Первый статический этап закрылся при ошибке неверной опции `MkDocs`.
Чистый повтор прошёл 22 из 22 проверок.

Исходный журнал сборки не сохранился во временном каталоге.
`image-build.log` явно обозначен как реконструкция происхождения уже
проверенного исходного образа через `docker image inspect` и
`docker image history`. Отдельная повторная сборка не используется как
доказательство идентичности.

## Границы

```text
qwake_slice=QW-LC4-F
qwake_status=runtime_authorization_frozen_execution_not_performed
qwake_next_slice=QW-LC4-F-merge
qwake_post_merge_next_slice=QW-LC4-E
QW_LC4_F_MATERIALIZED=true
QW_LC4_F_COMPLETE=false
QW_LC4_E_BRANCH_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
```

## Последствия

После коммита разрешён только PR фиксации `QW-LC4-F`. Разрешение нельзя
использовать на этой ветке. После слияния требуется отдельная независимая
проверка точного дерева, пакета и закрытых границ.

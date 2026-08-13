# ADR-131: репозиторная интеграция нового зафиксированного запроса `C1`

[English version](ADR-131-stage3b-qwake-c1-hostfix-request-freeze-repository-integration_EN.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-c1-hostfix-image-bound-request-freeze-v1/repository-integration.json -->

Нормативные термины:
[попытка](../glossary.md#term-attempt),
[выполнение](../glossary.md#term-execution),
[доказательные материалы](../glossary.md#term-evidence),
[фиксация](../glossary.md#term-freeze),
[роль кампании](../glossary.md#term-campaign-role),
[набор данных](../glossary.md#term-dataset) и
[доступ к тестовому набору данных](../glossary.md#term-test-dataset-access).

## Статус

Принято как репозиторная интеграция уже зафиксированного и независимо
проверенного запроса `C1_COLLECTION`. Эта запись не создаёт новую попытку
`Attempt-002`, не разрешает выполнение C1 и не изменяет байты запроса,
пререгистрации или внешних доказательных материалов.

## Связанная цепочка

Каноническая вершина репозитория и доказательных материалов:
`4e8f293d209bdc1661f8fca9095e5c522673b559` / `d58d96865f35c1f387f9b3406380f238280cd7da`.
Исполняемый исходный код, запечённый в образ:
`98cff5b2ecd64e1c96e19f0b04104ac00a5c3cf2`.
Научный образ: `sha256:12a4a6792530471517e53b30625bcfc45031a97bb9072f54bfa0c966e3fc2b5d`.
Фиксация образа: `sha256:ea207e6d31507d449e24fc30bb74fb21ec6560b1ec4a777cb1199de3ad63184f`.
Репозиторная интеграция образа:
`sha256:66369e9f6f666e94625f403c341028ae2249a7e74707c22b0fef75231b67fc46`.

Пререгистрация: `sha256:ed82a638b31761364f06fd460bec64bb668f6a9cb4bd077af53339dfd479048b`.
Семантическая идентичность запроса: `sha256:af7c27ec0db83d907b51361a8bb726db51f41fdbdc6bc341156b420648c606fd`.
Файловая идентичность запроса: `sha256:41bdb53052e03476ba908bf1ee1cbda0cda231c06361fcb6031848d857e0f19b`.
Фиксация запроса: `sha256:7fe57faefcc3aa92463e01422546e015e02e7a68c13dbbc9df1ef9feb7452b82`.

## Решение

1. Семь исходных файлов доказательных материалов фиксации запроса копируются
   побайтно; исходный `SHA256SUMS` с идентичностью
   `sha256:fab9a28dcc6c47fa84b905740f64c09f3aaed2afd3a4cfbd78aa34c8fa8ae858` сохраняется неизменным.
2. Внешние доказательные материалы считаются непрозрачной побайтно сохраняемой
   поверхностью. Для зафиксированных `.log` действует ограниченное каталогом
   правило `.gitattributes` со значением `binary`, поэтому добавление в индекс и
   фиксация коммита не нормализуют окончания строк.
3. Репозиторная оболочка связывает доказательные материалы с авторизацией
   интеграции, независимой проверкой только для чтения и хешем интеграции
   `sha256:9bffb8d2bc2516d1075c2a4615c4140b18b2eb2cc9068bac7581a1c7ed001e8f`.
4. `request.json` и `preregistration-manifest.json` не изменяются и не
   создаются повторно.
5. Прежний запрос C1 остаётся историческим и не подлежит повторному
   использованию.
6. Новый запрос уже зафиксирован, но авторизация его выполнения не выдана и
   `ATTEMPT002_CREATED=false`.
7. `Docker` и образ не изменяются; научное выполнение, доступ к тестовому
   набору данных и публикация остаются закрытыми.
8. После слияния и отдельной послеслияния проверки следующей границей может
   быть только отдельная авторизация выполнения попытки `C1 Attempt-002`.

## Проверяемая граница

```text
CANONICAL_REPOSITORY_MAIN=4e8f293d209bdc1661f8fca9095e5c522673b559
BAKED_IMAGE_SOURCE_COMMIT=98cff5b2ecd64e1c96e19f0b04104ac00a5c3cf2
IMAGE_DIGEST=sha256:12a4a6792530471517e53b30625bcfc45031a97bb9072f54bfa0c966e3fc2b5d
IMAGE_FREEZE_SHA256=sha256:ea207e6d31507d449e24fc30bb74fb21ec6560b1ec4a777cb1199de3ad63184f
C1_REQUEST_SHA256=sha256:af7c27ec0db83d907b51361a8bb726db51f41fdbdc6bc341156b420648c606fd
C1_REQUEST_FILE_SHA256=sha256:41bdb53052e03476ba908bf1ee1cbda0cda231c06361fcb6031848d857e0f19b
C1_REQUEST_FREEZE_SHA256=sha256:7fe57faefcc3aa92463e01422546e015e02e7a68c13dbbc9df1ef9feb7452b82
PREREGISTRATION_MANIFEST_SHA256=sha256:ed82a638b31761364f06fd460bec64bb668f6a9cb4bd077af53339dfd479048b
C1_REQUEST_FREEZE_INDEPENDENTLY_VERIFIED=true
ORIGINAL_EVIDENCE_BYTES_PRESERVED=true
ORIGINAL_EVIDENCE_FILE_COUNT=7
PREVIOUS_C1_REQUEST_REUSABLE=false
REQUEST_FREEZE_AUTHORIZATION_RECONSUMED=false
NEW_C1_REQUEST_FROZEN=true
NEW_C1_EXECUTION_AUTHORIZATION_ISSUED=false
ATTEMPT002_CREATED=false
C1_COLLECTION_OPEN=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=merge-post-merge-verify-then-authorize-C1-Attempt-002-execution
```

Хеш репозиторной интеграции: `sha256:9bffb8d2bc2516d1075c2a4615c4140b18b2eb2cc9068bac7581a1c7ed001e8f`.

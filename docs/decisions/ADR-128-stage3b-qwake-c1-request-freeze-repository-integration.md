# ADR-128: репозиторная интеграция зафиксированного запроса `C1`

[English version](ADR-128-stage3b-qwake-c1-request-freeze-repository-integration_EN.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-fresh-corrected-image-bound-c1-request-freeze-v1/repository-integration.json -->

Нормативные термины:
[выполнение](../glossary.md#term-execution),
[доказательные материалы](../glossary.md#term-evidence),
[фиксация](../glossary.md#term-freeze),
[роль кампании](../glossary.md#term-campaign-role),
[набор данных](../glossary.md#term-dataset) и
[доступ к тестовому набору данных](../glossary.md#term-test-dataset-access).

## Статус

Принято как репозиторная интеграция уже зафиксированного и независимо
проверенного запроса `C1_COLLECTION`. Этот срез не изменяет запрос или
пререгистрационный манифест, не перевыпускает фиксацию и не выдаёт разрешение
на научное выполнение.

## Связанная цепочка

Каноническое состояние репозитория перед фиксацией запроса:
`ba771e77f3ecff23d9f22319f413a708d930ed6e` / `76c7244d522c381cbcb7ce8c7dd1b5553b7ad329`.

Исполняемый образ остаётся
`sha256:89703b0b37b2729855835a6ed19ba1ca397ae14614c318344bd7625d12c727ef`, построенный из исходного коммита
`3858d3a7e6d7b3401e999523bc6675dc7dd0223d` и зафиксированный как
`sha256:ce8c054c92df18512b2a88ac25148f44c15487d8c2d4e68d8751966ac17bf287`. Его репозиторная интеграция:
`sha256:70012413e1d6bd69dbad060cef0d4b19e0bfe2635eca4dbe746ccfc42544ae72`.

Пререгистрация `C1` имеет идентичность
`sha256:c9fa7efb2f6816a9f7f09c7acce7cdc2e531935b28c70d00774bf79c38d47a48`. Канонический запрос имеет семантическую
идентичность `sha256:7e238ed8a61b7d80e52d67eef8a5f3af6e0c889c81b885a28a98df237284442e`, файловую идентичность
`sha256:ee72e90ef7f1bef3abbe9d2fcea5cea6f7d203aa1138c5d2d1eb8c39fe9ab694` и фиксацию `sha256:340f46bae2ca11e679893464f9f430ac93f1af49d39606b57638ba714e131bcc`.

## Решение

1. Семь исходных файлов доказательных материалов фиксации запроса копируются в
   репозиторий побайтно; их исходный `SHA256SUMS` с хэшем
   `sha256:2b36093a310a81bacb8a46122481ae071c882008e16e1be8f192634739a531d9` сохраняется неизменным.
2. Репозиторная оболочка связывает их с авторизацией интеграции, свежей
   независимой проверкой только для чтения и хэшем интеграции `sha256:a053011096dee7c3b4e5690190bca1909b2bf325fc4352366728c6ef4129a433`.
3. `request.json` и `preregistration-manifest.json` не изменяются и не
   создаются повторно.
4. Историческая старая авторизация остаётся непотреблённой и
   непотребляемой; свежая авторизация фиксации запроса уже потреблена ровно
   один раз и не может быть потреблена повторно.
5. `C1_REQUEST_FROZEN=true`, однако `C1_EXECUTION_AUTHORIZATION_ISSUED=false`.
6. Выполнение `C1/C2/C3/R`, эффекты Docker, доступ к тестовому набору данных и
   публикация остаются закрытыми.
7. После слияния этого ADR и отдельной послеслияния проверки следующей границей
   может быть только отдельная авторизация выполнения `C1`.

## Проверяемая граница

```text
C1_REQUEST_SHA256=sha256:7e238ed8a61b7d80e52d67eef8a5f3af6e0c889c81b885a28a98df237284442e
C1_REQUEST_FILE_SHA256=sha256:ee72e90ef7f1bef3abbe9d2fcea5cea6f7d203aa1138c5d2d1eb8c39fe9ab694
C1_REQUEST_FREEZE_SHA256=sha256:340f46bae2ca11e679893464f9f430ac93f1af49d39606b57638ba714e131bcc
PREREGISTRATION_MANIFEST_SHA256=sha256:c9fa7efb2f6816a9f7f09c7acce7cdc2e531935b28c70d00774bf79c38d47a48
C1_REQUEST_FREEZE_INDEPENDENTLY_VERIFIED=true
ORIGINAL_EVIDENCE_BYTES_PRESERVED=true
ORIGINAL_EVIDENCE_FILE_COUNT=7
HISTORICAL_C1_REQUEST_FREEZE_AUTHORIZATION_CONSUMED=false
HISTORICAL_C1_REQUEST_FREEZE_AUTHORIZATION_CONSUMABLE=false
FRESH_REQUEST_FREEZE_AUTHORIZATION_CONSUMED=true
FRESH_REQUEST_FREEZE_AUTHORIZATION_RECONSUMED=false
C1_REQUEST_FROZEN=true
C1_EXECUTION_AUTHORIZATION_ISSUED=false
C1_COLLECTION_OPEN=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=merge-post-merge-verify-then-authorize-C1-execution-boundary
```

Хэш репозиторной интеграции: `sha256:a053011096dee7c3b4e5690190bca1909b2bf325fc4352366728c6ef4129a433`.

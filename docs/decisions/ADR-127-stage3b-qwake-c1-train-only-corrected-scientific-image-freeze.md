# ADR-127: репозиторная интеграция исправленного научного образа `C1`

[English version](ADR-127-stage3b-qwake-c1-train-only-corrected-scientific-image-freeze_EN.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-c1-train-only-corrected-scientific-image-freeze-v1/repository-integration.json -->

Нормативные термины:
[выполнение](../glossary.md#term-execution),
[среда выполнения](../glossary.md#term-runtime),
[доказательные материалы](../glossary.md#term-evidence),
[фиксация](../glossary.md#term-freeze),
[кандидат](../glossary.md#term-candidate),
[роль кампании](../glossary.md#term-campaign-role),
[набор данных](../glossary.md#term-dataset) и
[доступ к тестовому набору данных](../glossary.md#term-test-dataset-access).

## Статус

Принято как репозиторная интеграция уже построенного, проверенного,
зафиксированного и независимо проверенного исправленного научного образа,
устраняющего выявленную ADR-126 зависимость C1 от более широкой поверхности
конструктора набора данных. Этот срез не строит и не запускает Docker-образ,
не фиксирует запрос C1 и не открывает научную кампанию.

## Историческая граница

ADR-123 и образ `QW-5` v1
`sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3` остаются неизменяемой исторической
фиксацией. ADR-125 и образ
`sha256:7aefbc241ad725f4ac31d8b72c63a82247516ad4831aad6f7d0ef89817f9dacb` также сохраняются без изменения:
они документируют корректно построенный замещающий оркестраторный образ, но
ADR-126 установил, что этот образ нельзя считать допустимым для C1 из-за
недостаточно узкой изоляции тестовых ресурсов в тракте данных.

ADR-126 был слит как `3858d3a7e6d7b3401e999523bc6675dc7dd0223d` /
`f516667472e1ea2a8e2826f520c055cfe2dd0351` и перенёс изоляцию под контроль проекта: запрос может связывать
только два канонических несжатых обучающих `IDX`-файла, а научная среда
выполнения больше не использует конструктор `torchvision` набора данных.

Исправленный образ `sha256:89703b0b37b2729855835a6ed19ba1ca397ae14614c318344bd7625d12c727ef` был построен ровно один раз из
этого состояния, прошёл 157-путевую проверку замыкания, отдельную проверку изоляции только обучающих
данных `5 passed`, прежнюю целевую проверку `45 passed`, `pip check` и
проверку отсутствия полезной нагрузки набора данных. После этого он был зафиксирован как
`sha256:ce8c054c92df18512b2a88ac25148f44c15487d8c2d4e68d8751966ac17bf287` и независимо проверен без `docker run` и без
повторной сборки.

## Решение

1. После слияния этой интеграции и независимой послеслияния проверки единственным
   операционным научным образом для будущих `C1_COLLECTION`, `C2_CALIBRATION`,
   `C3_CONFIRMATORY` и `R_REPLICATION` становится
   `sha256:89703b0b37b2729855835a6ed19ba1ca397ae14614c318344bd7625d12c727ef`.
2. Образ связан с исходным коммитом `3858d3a7e6d7b3401e999523bc6675dc7dd0223d`, деревом `f516667472e1ea2a8e2826f520c055cfe2dd0351`,
   манифестом среды выполнения `sha256:01d86f045bf42554382654d2c48f2be23f4763b6fbdc4aa1c9e7cff939367561` и
   исправленной реализацией `sha256:94cb8b210dcde5b4b2a71ed85c60938eb748727af9ef0a8d1bdb958b4739c4f4`.
3. ADR-127 заменяет операционное решение ADR-125 для будущих кампаний, но не
   изменяет исторические факты, байты или статусы ADR-123, ADR-125 и их образов.
4. Исходные 18 файлов доказательных материалов копируются в репозиторий
   побайтно. Их исходный `SHA256SUMS` с хэшем `sha256:8854315bc989b1d62feda4fca07a6a0b5ee5bbd529a322f6579cd199ce0a0271`
   сохраняется неизменным; репозиторная оболочка дополнительно связывает
   авторизацию интеграции и свежую независимую проверку.
5. Один и тот же идентификатор исправленного образа обязателен для `C1/C2/C3/R`.
6. Ранее выданная авторизация на фиксацию запроса C1 остаётся непотреблённой.
   Этот срез её не использует. Возврат к этой границе разрешён только после
   слияния ADR-127 и отдельной послеслияния проверки.
7. `C1` этим решением не запускается. Разрешение на выполнение C1 остаётся
   отдельной последующей границей.
8. Научное выполнение, доступ к тестовому набору данных и публикация остаются
   закрытыми.

## Проверяемая граница

```text
QW5_V1_HISTORICAL_FREEZE_PRESERVED=true
PREVIOUS_SUPERSEDING_IMAGE_PRESERVED=true
PREVIOUS_SUPERSEDING_IMAGE_DIGEST=sha256:7aefbc241ad725f4ac31d8b72c63a82247516ad4831aad6f7d0ef89817f9dacb
PREVIOUS_SUPERSEDING_IMAGE_C1_ADMISSIBLE=false
CORRECTED_SCIENTIFIC_IMAGE_DIGEST=sha256:89703b0b37b2729855835a6ed19ba1ca397ae14614c318344bd7625d12c727ef
CORRECTED_SCIENTIFIC_IMAGE_FREEZE_SHA256=sha256:ce8c054c92df18512b2a88ac25148f44c15487d8c2d4e68d8751966ac17bf287
CORRECTED_SCIENTIFIC_IMAGE_FREEZE_INDEPENDENTLY_VERIFIED=true
TRAIN_ONLY_ISOLATION_VALIDATED=true
RUNTIME_SOURCE_MANIFEST_SHA256=sha256:01d86f045bf42554382654d2c48f2be23f4763b6fbdc4aa1c9e7cff939367561
CORRECTION_IMPLEMENTATION_SHA256=sha256:94cb8b210dcde5b4b2a71ed85c60938eb748727af9ef0a8d1bdb958b4739c4f4
ORIGINAL_EVIDENCE_BYTES_PRESERVED=true
ORIGINAL_EVIDENCE_FILE_COUNT=18
SAME_IMAGE_DIGEST_REQUIRED_ACROSS_C1_C2_C3_R=true
C1_REQUEST_FREEZE_AUTHORIZATION_PREVIOUSLY_ISSUED=true
C1_REQUEST_FREEZE_AUTHORIZATION_CONSUMED=false
C1_REQUEST_FREEZE_PERMITTED=false
C1_REQUEST_FROZEN=false
C1_EXECUTION_AUTHORIZATION_ISSUED=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=merge-post-merge-verify-then-resume-existing-C1-request-freeze-boundary
```

Хэш репозиторной интеграции: `sha256:70012413e1d6bd69dbad060cef0d4b19e0bfe2635eca4dbe746ccfc42544ae72`.

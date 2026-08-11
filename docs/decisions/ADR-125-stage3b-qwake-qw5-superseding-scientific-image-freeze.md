# ADR-125: фиксация замещающего научного образа `QW-5`

[English version](ADR-125-stage3b-qwake-qw5-superseding-scientific-image-freeze_EN.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-qw5-superseding-scientific-image-freeze-v1/repository-integration.json -->

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

Принято как репозиторная интеграция уже построенного, проверенного, зафиксированного
и независимо проверенного замещающего научного образа `QW-5`. Этот срез не
строит и не запускает Docker-образ и не открывает научную кампанию.

## Историческая граница

ADR-123 и образ версии 1
`sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3` остаются неизменяемой исторической
фиксацией. Они не удаляются и не переинтерпретируются. ADR-124 установил, что
версия 1 не содержит заранее зарегистрированной точки запуска научной кампании,
поэтому для будущего `C1` был необходим замещающий образ.

Замещающий образ был один раз построен из канонических слитых исходников
`95a0bf35c87f87ee836596c02ab90a71703714f3` / `e0fdaa3214f4a39b92e82e2d2529c6c506513166`, прошёл проверку 157-путевого
замыкания среды выполнения и целевой набор тестов `45 passed`, после чего был
зафиксирован и независимо проверен без повторной сборки.

## Решение

1. Для всех **будущих** `C1_COLLECTION`, `C2_CALIBRATION`,
   `C3_CONFIRMATORY` и `R_REPLICATION` единственным допустимым научным образом
   является `sha256:7aefbc241ad725f4ac31d8b72c63a82247516ad4831aad6f7d0ef89817f9dacb`.
2. Семантический хэш его фиксации:
   `sha256:47c20698ac57c1b50f4bbe0314649b0d07494ecc1199b32819ecde7b684d9904`.
3. Образ связан с исходным коммитом `95a0bf35c87f87ee836596c02ab90a71703714f3`, исходным деревом
   `e0fdaa3214f4a39b92e82e2d2529c6c506513166`, манифестом среды выполнения
   `sha256:d6e3bdf33b868334062dd6e12e958392a61f8101b5f0410353f39f20338d6c3d` и точной реализацией
   `sha256:2047bf5ba1c2555dcea54efd3381ef35c16411ba7efbe84a75116858187708fa`.
4. ADR-125 заменяет операционное решение ADR-123 о научном образе для будущих
   кампаний, но не изменяет исторические факты, байты или статус `QW-5` v1.
5. Исходный пакет доказательных материалов копируется в репозиторий побайтно;
   его внутренний `SHA256SUMS` сохраняется неизменным. Репозиторная оболочка
   дополнительно связывает независимую проверку и авторизацию интеграции.
6. Один и тот же идентификатор замещающего образа обязателен для `C1/C2/C3/R`.
7. `C1` этим решением не открывается. Следующая отдельная граница — фиксация
   запроса `C1` и его разрешение на выполнение, связанные с этой фиксацией.
8. Научное выполнение, доступ к тестовому набору данных и публикация остаются
   закрытыми.

## Проверяемая граница

```text
QW5_V1_HISTORICAL_FREEZE_PRESERVED=true
QW5_V1_IMAGE_DIGEST=sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3
QW5_V1_CORRECTIVE_FREEZE_SHA256=sha256:b435c09c02783f09156cfb7f68045151aa659e144e3c95d85480cee99020f6f4
SUPERSEDING_QW5_IMAGE_DIGEST=sha256:7aefbc241ad725f4ac31d8b72c63a82247516ad4831aad6f7d0ef89817f9dacb
SUPERSEDING_QW5_FREEZE_SHA256=sha256:47c20698ac57c1b50f4bbe0314649b0d07494ecc1199b32819ecde7b684d9904
SUPERSEDING_QW5_SOURCE_COMMIT=95a0bf35c87f87ee836596c02ab90a71703714f3
SUPERSEDING_QW5_SOURCE_TREE=e0fdaa3214f4a39b92e82e2d2529c6c506513166
RUNTIME_SOURCE_MANIFEST_SHA256=sha256:d6e3bdf33b868334062dd6e12e958392a61f8101b5f0410353f39f20338d6c3d
ORCHESTRATOR_IMPLEMENTATION_SHA256=sha256:2047bf5ba1c2555dcea54efd3381ef35c16411ba7efbe84a75116858187708fa
SUPERSEDING_IMAGE_FREEZE_INDEPENDENTLY_VERIFIED=true
ORIGINAL_EVIDENCE_BYTES_PRESERVED=true
SAME_IMAGE_DIGEST_REQUIRED_ACROSS_C1_C2_C3_R=true
C1_REQUEST_FROZEN=false
C1_EXECUTION_AUTHORIZATION_ISSUED=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=merge-post-merge-verify-then-C1-request-freeze-and-authorization
```

Хэш репозиторной интеграции:
`sha256:e35d1c90c3dc118c3a1514a62c7487196c48482de4cb1aae74e9ba942b2b518c`.

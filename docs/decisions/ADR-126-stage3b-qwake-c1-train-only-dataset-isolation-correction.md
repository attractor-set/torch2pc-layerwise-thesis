# ADR-126: коррекция изоляции только обучающих данных для C1

[English version](ADR-126-stage3b-qwake-c1-train-only-dataset-isolation-correction_EN.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-c1-train-only-dataset-isolation-correction-v1/implementation.json -->

Нормативные термины:
[выполнение](../glossary.md#term-execution),
[среда выполнения](../glossary.md#term-runtime),
[доказательные материалы](../glossary.md#term-evidence),
[фиксация](../glossary.md#term-freeze),
[роль кампании](../glossary.md#term-campaign-role),
[набор данных](../glossary.md#term-dataset) и
[доступ к тестовому набору данных](../glossary.md#term-test-dataset-access).

## Статус

Принято как подготовка минимальной коррекции тракта только обучающих данных, необходимой
до фиксации запроса C1. Этот срез не строит и не запускает образ, не фиксирует
запрос C1, не выдаёт разрешение на выполнение C1, не выполняет научную кампанию,
не обращается к тестовым данным и не разрешает публикацию.

## Результат проверки допуска

После слияния и независимой проверки ADR-125 / PR #197 в состоянии
`2d748751482a6b3ecb200fb3816d41f48d8ed8cc` /
`f6ce596c2d7ff45a054ed8c0bb5d6ceb3cc3b97d` проверка допуска к фиксации запроса
C1 осталась закрытой по умолчанию. Проектная среда выполнения перед материализацией только обучающих данных
делегировала создание рабочего обучающего набора данных конструктору `torchvision` семейства
MNIST. Поскольку `test_dataset_access=false` запрещает чтение тестовых данных,
для изоляции C1 отсутствовало достаточное проектное основание в тракте выполнения.
Ранее выданная авторизация на фиксацию запроса C1 остаётся непотреблённой.

## Решение

1. Сохранить образ `sha256:7aefbc241ad725f4ac31d8b72c63a82247516ad4831aad6f7d0ef89817f9dacb` и его фиксацию
   `sha256:47c20698ac57c1b50f4bbe0314649b0d07494ecc1199b32819ecde7b684d9904`
   неизменными как историческое доказательство. Не переинтерпретировать этот
   образ как готовый к C1.
2. Ограничить `ScientificDatasetBinding` ровно двумя каноническими
   несжатыми ресурсами обучающих данных: `train-images-idx3-ubyte`, затем
   `train-labels-idx1-ubyte` под `data/<dataset-name>/raw/`. `t10k-*`, сжатая
   альтернатива, отсутствующий или лишний ресурс и иной порядок недопустимы.
3. Полностью убрать конструктор `torchvision` набора данных из научной среды выполнения.
   Разбирать только два уже проверенных по хэшу связанных `IDX`-файла. Требовать магическое число
   2051 для изображений, 2049 для меток, геометрию 28×28, точную длину полезной нагрузки и
   одинаковое число изображений и меток.
4. Явно сохранить прежнюю семантику преобразования: `uint8` переводится в `float32`
   делением на 255, затем добавляется нулевое дополнение по два пикселя с каждой
   стороны, результат имеет форму `1x32x32`.
5. Добавить состязательную проверку с реально существующими файлами-ловушками `t10k-*`:
   любое открытие тестового ресурса должно приводить к ошибке. Добавить отрицательные
   проверки схемы запроса и повреждённых `IDX`.
6. Не менять исторический манифест среды выполнения оркестратора. Создать новую
   перспективную 157-путевую замкнутость в
   `experiments/frozen/stage3b-qwake-c1-train-only-dataset-isolation-correction-v1/runtime-SHA256SUMS` с хэшем `sha256:01d86f045bf42554382654d2c48f2be23f4763b6fbdc4aa1c9e7cff939367561`.
7. Не строить образ в этом срезе. После слияния и независимой послеслияния проверки
   потребуется отдельная авторизация на сборку, проверку и фиксацию исправленного
   образа. Только после этого можно вернуться к уже выданной границе фиксации запроса C1.


## Проверяемая граница

```text
C1_ADMISSION_AUDIT_V1_SHA256=sha256:119113ab83b2622ab0e005bc16318bf88fc4e41ced56ad183c10813d5e63f784
C1_TRAIN_ONLY_DATASET_ISOLATION_CORRECTION_AUTHORED=true
REQUEST_SCHEMA_EXACT_TRAIN_ASSET_COUNT=2
REQUEST_SCHEMA_TEST_RESOURCE_BINDING_PERMITTED=false
TORCHVISION_DATASET_CONSTRUCTOR_IN_SCIENTIFIC_RUNTIME=false
TRAIN_ONLY_IDX_PARSER=true
ADVERSARIAL_T10K_OPEN_TRAP_TEST=true
RUNTIME_SOURCE_PATH_COUNT=157
RUNTIME_SOURCE_MANIFEST_SHA256=sha256:01d86f045bf42554382654d2c48f2be23f4763b6fbdc4aa1c9e7cff939367561
CURRENT_SUPERSEDING_IMAGE_PRESERVED=true
CURRENT_SUPERSEDING_IMAGE_C1_ADMISSIBLE=false
NEW_SCIENTIFIC_IMAGE_REQUIRED=true
NEW_SCIENTIFIC_IMAGE_BUILT=false
C1_REQUEST_FREEZE_AUTHORIZATION_CONSUMED=false
C1_REQUEST_FROZEN=false
C1_EXECUTION_AUTHORIZATION_ISSUED=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=merge-post-merge-verify-then-corrected-image-build-validation-freeze
```

Самохэш реализации: `sha256:85ae69d5f39b898e1645e5088d67ad39378484d1a7506e92ae08d4d8d9f2033b`.

# ADR-123: единая фиксация научного образа `QW-5`

[English version](ADR-123-stage3b-qwake-qw5-single-scientific-image-freeze_EN.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-fp-scientific-image-freeze-corrective-v1/freeze.json -->

Нормативные термины:
[попытка](../glossary.md#term-attempt),
[выполнение](../glossary.md#term-execution),
[запуск](../glossary.md#term-run),
[среда выполнения](../glossary.md#term-runtime),
[доказательные материалы](../glossary.md#term-evidence),
[фиксация](../glossary.md#term-freeze),
[кандидат](../glossary.md#term-candidate),
[доступ к тестовому набору данных](../glossary.md#term-test-dataset-access) и
[набор данных](../glossary.md#term-dataset).

## Статус

Принято как материализованная и независимо проверенная корректирующая фиксация
единственного научного образа `QW-5`. Научная кампания этим решением не
запускается.

## Историческая граница

`Attempt-001` пересёк границу необратимого действия и один раз успешно построил
образ, однако исходная статическая проверка завершилась ошибкой до
материализации `freeze.json`. Поэтому `Attempt-001` остаётся терминальной
неуспешной попыткой: она не повторялась, не исправлялась задним числом и не
переинтерпретируется как успешная.

Сохранившийся неизменяемый
[кандидат](../glossary.md#term-candidate)
`sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3` был позднее проверен отдельной корректирующей процедурой.
Полный набор тестов дал `1659 passed, 8 skipped`; проверка зависимостей,
побайтовая сверка исполняемых исходников и проверка отсутствия полезной нагрузки
набора данных завершились успешно. Полученные доказательные материалы были
сохранены, независимо проверены, отдельно рассмотрены и затем снова независимо
проверены.

## Решение

1. Единственным научным образом для `C1/C2/C3/R` является
   `sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3`.
2. Образ связан с исходным коммитом `4eb23b6f5e2e3b2f3cdee83a4732f8a091b7b662`, деревом `1db3999089bf15d153a0a83920f6c1e9a1431218` и
   неизменяемым идентификатором базового образа
   `rocm/pytorch@sha256:96a2fb24dec9896e2f8238178f0c49d0dcc4c7dcc597be09e4564316bd86d191`.
3. Семантический хэш корректирующей фиксации:
   `sha256:b435c09c02783f09156cfb7f68045151aa659e144e3c95d85480cee99020f6f4`.
4. `Attempt-001` сохраняет состояния `terminal=true`, `success=false`,
   `reinterpreted=false`, `retry_performed=false`.
5. Исходный сценарий `QW-5` повторно не запускался; отсутствующие исходные
   артефакты статической проверки не создавались задним числом.
6. После фиксации исполняемые исходники и зависимости не изменяются.
7. Один и тот же идентификатор образа обязателен для `C1_COLLECTION`,
   `C2_CALIBRATION`, `C3_CONFIRMATORY` и `R_REPLICATION`.
8. `QW-5` не открывает `C1`; следующая отдельная граница — фиксация запроса
   `C1` и его авторизация, связанные с этой корректирующей фиксацией.
9. Доступ к тестовому набору данных, научное выполнение и публикация остаются
   закрытыми.

## Проверяемая граница

```text
QW_LC4_E_COMPLETE=true
QW5_IMAGE_FROZEN=true
QW5_FREEZE_MODE=corrective_evidence
QW5_IMAGE_DIGEST=sha256:800471114a6fec7d401fcbc3c781957265aaa351babaa5adf823d1521a95a8e3
QW5_SOURCE_COMMIT=4eb23b6f5e2e3b2f3cdee83a4732f8a091b7b662
QW5_SOURCE_TREE=1db3999089bf15d153a0a83920f6c1e9a1431218
QW5_CORRECTIVE_FREEZE_SHA256=sha256:b435c09c02783f09156cfb7f68045151aa659e144e3c95d85480cee99020f6f4
ATTEMPT001_TERMINAL=true
ATTEMPT001_SUCCESS=false
ATTEMPT001_REINTERPRETED=false
ATTEMPT001_RETRY_PERFORMED=false
EXECUTION_IMAGE_STRATEGY=single_immutable_superset_image
SAME_IMAGE_DIGEST_REQUIRED_ACROSS_C1_C2_C3_R=true
EXECUTABLE_CODE_CHANGES_AFTER_IMAGE_FREEZE=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=C1-request-freeze-and-authorization
```

Цепочка доказательств:
- квитанция корректирующей проверки:
  `sha256:7ee321d1feeda213828c67151e08ccb470d8ab52cf088ad6bff8e10269cc10e2`;
- журнал корректирующей проверки:
  `sha256:86a2b8e662f519fc28fbe292f36b1997a9f956aa18f69c3ce1ed7383749d2bd7`;
- решение по корректирующей проверке:
  `sha256:e345db724703607cc4d22c4428d480c6eec6820f31be657eb6a86ac7f556dea1`;
- авторизация корректирующей фиксации:
  `sha256:505b995dba38da25bf2724a043166cb3f3c85e5a43c34370084a3f62582b0ba3`;
- корректирующая фиксация:
  `sha256:b435c09c02783f09156cfb7f68045151aa659e144e3c95d85480cee99020f6f4`.

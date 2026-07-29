# ADR-078: запись операции одноразового инженерного вызова `QW-LC4-E`

[English version](ADR-078-stage3b-qwake-lc4-e-one-shot-engineering-invocation-operation_EN.md)

- **Статус:** принят как авторинг операции; [выполнение](../glossary.md#term-execution) не начато
- **Дата:** 29 июля 2026 года
- **Базовый коммит:** `28be77706bc86abaf34f86e9bdcbdcb9cc2810a8`

## Контекст

PR №138 завершил слияние допуска одноразового инженерного вызова. Допуск
связывает авторизацию, неизменяемый образ, Torch2PC и ограниченный хостовый
исполнитель, но намеренно оставляет проверку текущей рабочей среды и [запуск](../glossary.md#term-run)
отдельной операторской операцией.

Перед такой операцией требуется неизменяемая запись, которая определяет точные
динамические входы и проверки запуска, не выполняя их во время авторинга.

## Решение

Материализовать двухфайловый пакет
`stage3b-qwake-lc4-e-one-shot-engineering-invocation-operation-v1`, чистый
модуль проверки, `CLI`-проверку и отрицательные тесты. Запись операции:

1. связывает коммит слияния PR №138, его родителей и полный пакет допуска;
2. повторно связывает одноразовую авторизацию, образ, Torch2PC и реализацию
   хостового исполнителя;
3. фиксирует точный набор из 13 ключей ресурсов хоста;
4. требует при будущем запуске два одинаковых `image inspection`, две одинаковые
   материализации канонического `argv`, отсутствие `lease`, результата и
   `staging`, а также непотреблённую авторизацию;
5. ограничивает хостовый запуск одним `Popen`, запрещает оболочку и автоматический
   повтор после попытки запуска;
6. сохраняет `PREEXECUTION_IDENTITY_VERIFIED=false`, потому что текущий образ,
   ресурсы хоста и время захвата ещё не проверялись;
7. сохраняет все эффекты рабочей среды закрытыми.

Проверяющий модуль не импортирует функцию вызова, не выполняет `image inspection`,
не материализует команду, не создаёт дочерний процесс и не записывает файл
владения или результат.

## Идентичности

```text
operation_base_commit=28be77706bc86abaf34f86e9bdcbdcb9cc2810a8
admission_head_commit=a26419057c133972b18a728575426ef510bcf360
admission_parent_commit=3454d12d3cc16c9c50977e2a598e2bc1a8768441
admission_merged_at_utc=2026-07-29T18:08:53Z
admission_sha256=sha256:fe07bc20bf5866d84730df945c2ababc7b5f4f255648c5de6e3185ba4e37c01d
operation_sha256=sha256:10a612ef1b765362b361ecea57923d00a9f7339c9d3f9e3b27337f92f15326e9
operation_file_sha256=sha256:b8cabec098b14f1007adc9fa660fa1e31af9501f2266219aca3ddec24129f610
package_registry_sha256=sha256:eeb417ba5d2c72dc198b22be69ea1d933da5bb03245615d418bbf0a6ba15edbd
module_sha256=sha256:f653468c77494205a6daf7af6ea3cd151260c9b9479b9a02f0a41949a0a5ab30
verifier_sha256=sha256:a51b22004bb8da9611538c01bf718710e5a6eda4111b3dec44aa7dbcb777448c
test_sha256=sha256:bc11ec8443cf7432bb89d6ebbf1698448125c30e3ae74331347a866be17d4458
```

## Границы

```text
REPOSITORY_FREEZE_COMPLETE=true
INVOCATION_ADMISSION_COMPLETE=true
INVOCATION_OPERATION_RECORD_PRESENT=true
PREEXECUTION_IDENTITY_CHECKS_IMPLEMENTED=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_OPERATION_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Последствия

Следующий отдельный срез должен зафиксировать и слить эту запись. Только после
независимой проверки после слияния допустима отдельная операция выполнения с эффектами рабочей среды,
которая либо завершит все динамические проверки и выполнит ровно одну попытку,
либо завершится закрыто без запуска.

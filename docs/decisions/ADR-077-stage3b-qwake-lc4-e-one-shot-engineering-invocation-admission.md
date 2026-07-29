# ADR-077: допуск одноразового инженерного вызова `QW-LC4-E`

[English version](ADR-077-stage3b-qwake-lc4-e-one-shot-engineering-invocation-admission_EN.md)

- **Статус:** принят как авторинг допуска; [выполнение](../glossary.md#term-execution) не начато
- **Дата:** 29 июля 2026 года
- **Базовый коммит:** `3454d12d3cc16c9c50977e2a598e2bc1a8768441`

## Контекст

PR №137 завершил фиксацию репозитория хостового исполнителя. Разрешение одного
будущего вызова уже существует, а исполнитель способен выполнить точный
`docker run`. Эти факты не разрешают немедленный [запуск](../glossary.md#term-run): перед отдельной
операторской операцией требуется связать точный `merge commit`, неизменяемую
авторизацию, реализацию исполнителя, образ, Torch2PC и закрытое состояние
результата и файла владения.

## Решение

Материализовать двухфайловый пакет
`stage3b-qwake-lc4-e-one-shot-engineering-invocation-admission-v1`, чистый
модуль проверки, `CLI`-проверку и отрицательные тесты. Допуск:

1. связывает `merge commit` PR №137 и оба родителя;
2. повторно проверяет точный пакет разрешения одноразового вызова;
3. повторно проверяет `semantic state` и `frozen package` хостового исполнителя;
4. требует будущую двойную проверку локального образа, `host resources`,
   отсутствия `lease`, результата и `staging` непосредственно в операторской операции;
5. сохраняет `preexecution_identity_verified=false`, потому что рабочая среда
   ещё не проверялась;
6. сохраняет веточное разрешение и все эффекты рабочей среды закрытыми.

Проверяющий модуль не импортирует функцию вызова, не выполняет `image inspection`,
не материализует команду и не создаёт дочерний процесс.

## Идентичности

```text
invocation_base_commit=3454d12d3cc16c9c50977e2a598e2bc1a8768441
repository_freeze_head=cc287334a325f460555bab06725c52ba548985eb
repository_freeze_parent=da51c8d858c541372525125640db99062041fc20
invocation_authorization_sha256=sha256:0a60dacc1bfd5073cf52d76f2ec33ae54f00899aad9877d44607199659fda75a
host_runtime_invoker_implementation_sha256=sha256:1f5f31d4f220bbf074736f1de0b78a5dafa2849188ac337704d5cc704668fdf4
host_runtime_invoker_contract_sha256=sha256:607bf719d8a976569c50d7cfe8604ab341843dad00d3eef8784e1dc6cfd9b88d
image_repo_digest=torch2pc-layerwise-thesis@sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d
admission_sha256=sha256:fe07bc20bf5866d84730df945c2ababc7b5f4f255648c5de6e3185ba4e37c01d
admission_file_sha256=sha256:319f415265d041d883c3980f884dcb736f6f236a90ed3777c65e1ae10b7c9bba
package_registry_sha256=sha256:bc4bacb646759e8fa42caf336229a647e7a6d87a9ba292faf38ca9055b3b6ac2
module_sha256=sha256:53264f77a5e72fa4933f0a68825c07dcde01b7e2d362de0cba1b4394113c436f
verifier_sha256=sha256:06f61646988f7798cc57a47796fe0d5f4fff12f3d2fe4c5536b8f64617cd2148
test_sha256=sha256:ff9841329831bbfe84fb0fa571ef5f1a6ab6209b97a4e20f51a1ee68bd4f5b3f
```

## Границы

```text
REPOSITORY_FREEZE_COMPLETE=true
INVOCATION_ADMISSION_RECORD_PRESENT=true
PREEXECUTION_IDENTITY_CHECKS_IMPLEMENTED=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERFORMED=false
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Последствия

Следующий отдельный срез должен слить и независимо проверить этот допуск. Только
после этого допустима отдельная операторская операция, которая повторно проверит
рабочую среду и либо выполнит ровно один вызов, либо завершится закрыто при ошибке.

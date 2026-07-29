# ADR-079: авторизация выполнения одноразового инженерного вызова `QW-LC4-E`

[English version](ADR-079-stage3b-qwake-lc4-e-one-shot-engineering-invocation-execution-authorization_EN.md)

- **Статус:** принят как авторинг авторизации; проверка рабочей среды и [выполнение](../glossary.md#term-execution) не начаты
- **Дата:** 29 июля 2026 года
- **Базовый коммит:** `b0f6729e8fd1cb1aa172eef488dc56e36b335173`

## Контекст

PR №139 завершил слияние записи операции одноразового инженерного вызова. Эта
запись фиксирует динамические входы и обязательные проверки будущего запуска,
но намеренно не разрешает веточное выполнение и не проверяет текущий образ,
ресурсы хоста, время захвата, файл владения, каталог результата или `staging`.

Перед отдельной проверкой рабочей среды требуется машиночитаемая авторизация,
которая связывает точный коммит слияния операции с ранее замороженным разрешением
и определяет, при каких условиях может быть допущен ровно один будущий вызов.

## Решение

Материализовать двухфайловый пакет
`stage3b-qwake-lc4-e-one-shot-engineering-invocation-execution-authorization-v1`,
чистый модуль проверки, `CLI`-проверку и отрицательные тесты. Авторизация:

1. связывает коммит слияния PR №139, головной коммит операции, его родителя и
   полный пакет `operation-v1`;
2. повторно связывает прежнюю одноразовую авторизацию, неизменяемый образ,
   Torch2PC и ограниченный хостовый исполнитель;
3. разрешает только будущую проверку перед выполнением и один будущий инженерный
   вызов, но не открывает выполнение на подготовительной ветке;
4. требует точные 13 ключей ресурсов хоста, два одинаковых `image inspection`,
   две одинаковые материализации канонического `argv` и не более одного
   `Popen` без оболочки;
5. требует непотреблённую авторизацию и отсутствие `lease`, результата и
   `staging` непосредственно перед [запуском](../glossary.md#term-run);
6. требует, чтобы динамическая проверка и [запуск](../glossary.md#term-run) находились в одном процессе,
   а хост не записывал файл владения и не выполнял автоматический повтор;
7. сохраняет `PREEXECUTION_IDENTITY_VERIFIED=false` и все эффекты рабочей среды
   закрытыми до отдельного среза после слияния.

Модуль не импортирует функцию вызова, не выполняет `image inspection`, не
материализует команду, не создаёт дочерний процесс и не записывает файл
владения, результат или [доказательные материалы](../glossary.md#term-evidence).

## Идентичности

```text
execution_base_commit=b0f6729e8fd1cb1aa172eef488dc56e36b335173
operation_head_commit=aa8886221e286a5881f2b720414859bb313c2867
operation_parent_commit=28be77706bc86abaf34f86e9bdcbdcb9cc2810a8
operation_merged_at_utc=2026-07-29T18:57:10Z
operation_sha256=sha256:10a612ef1b765362b361ecea57923d00a9f7339c9d3f9e3b27337f92f15326e9
execution_authorization_sha256=sha256:ff136538faee0d7952dc444e521d7ec760c7d54cd38406cb9b19ff1e00d9437b
authorization_file_sha256=sha256:11f12d2c2723902716ca9e7209f408b9edae2f793ceb098c8adeb06fee8c0c72
package_registry_sha256=sha256:4ab39c084f330d8679495f4aefdcc11005fc8d83a21b2a5c78cee80aeda562b5
module_sha256=sha256:2769982c9f36108f1cb70b43ab7cee9eea5a63ac870f5fb1d4d938800ee837f5
verifier_sha256=sha256:3a4f8f920b1d28036c9f1d690b98f492437de1c2e9ce5106baf102bd05f053bd
test_sha256=sha256:c1b226bc97d4fcd3c5db30ee0c581581dc65da57924c61cb19e4d65daeb29b59
```

## Границы

```text
REPOSITORY_FREEZE_COMPLETE=true
INVOCATION_ADMISSION_COMPLETE=true
INVOCATION_OPERATION_COMPLETE=true
EXECUTION_AUTHORIZATION_RECORD_PRESENT=true
EXECUTION_AUTHORIZATION_ISSUED=true
PREEXECUTION_VERIFICATION_MATERIALIZATION_IMPLEMENTED=true
PREEXECUTION_IDENTITY_VERIFIED=false
ONE_SHOT_ENGINEERING_INVOCATION_SLICE_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_OPERATION_OPEN=true
ONE_SHOT_ENGINEERING_INVOCATION_EXECUTION_OPEN=true
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

После фиксации и слияния этой авторизации отдельный срез может выполнить только
проверку перед выполнением текущей рабочей среды. Такая проверка обязана завершиться
закрыто при любом расхождении и не может сама создавать `lease` или запускать
контейнер. Фактический одноразовый вызов остаётся отдельной атомарной операцией.

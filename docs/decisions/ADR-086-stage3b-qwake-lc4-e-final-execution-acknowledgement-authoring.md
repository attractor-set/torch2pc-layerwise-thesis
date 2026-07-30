# ADR-086: подготовка финального подтверждения выполнения `QW-LC4-E`

[English version](ADR-086-stage3b-qwake-lc4-e-final-execution-acknowledgement-authoring_EN.md)

- **Статус:** принят как статический контракт подготовки; подтверждение не выпущено
- **Дата:** 2026-07-30
- **Базовый коммит:** `2957d8f6975c88e7bdb23243e3915c7f51d4ba47`

## Контекст

PR №146 связал хостовый исполнитель с точными сохранёнными байтами постоянного
файла владения v2 и был независимо проверен после слияния. Цепочка теперь
содержит атомарную запись файла владения, устойчивую терминальную квитанцию и
единственный перспективный вход без прямого обхода нижнего исполнителя.

Однако статическая готовность механизма не является финальным операторским
подтверждением. Автоматический переход от подготовленного контракта к
разрешённому вызову недопустим: подтверждение должно отдельно и однозначно
связать оператора, время, всю доказательную цепочку, образ, Torch2PC, каталог
результатов и одну необратимую попытку.

## Решение

1. Добавить статический пакет подготовки
   `stage3b-qwake-lc4-e-final-execution-acknowledgement-authoring-v1`.
2. Сохранить точную квитанцию проверки слияния PR №146: `39` направленных,
   `240` расширенных и `1287` полных тестов при `14` предупреждениях,
   обязательные проверки CI, Ruff, `mypy`, обе сборки документации, идентичность
   Torch2PC и закрытую границу рабочей среды.
3. Связать контракт подготовки с цепочкой
   `persistent-evidence-chain-v2`, её реализацией, привязкой хостового
   исполнителя, авторизацией вызова, авторизацией выполнения, проверкой перед
   выполнением, операцией рабочей среды и восстановлением её идентичности.
4. Требовать для будущего подтверждения точную фразу
   `ACKNOWLEDGE_QWAKE_LC4_FINAL_ONE_SHOT_EXECUTION`, непустую идентичность
   оператора и время по всемирному координированному времени строго после слияния PR №146.
5. Связать будущее подтверждение с точным неизменяемым образом, коммитом
   Torch2PC, каталогом результатов, путями файла владения v2 и устойчивой
   квитанции исхода, `invocation_count=1`, запретом повтора и одной попыткой.
6. Разделить подготовку, выпуск подтверждения и материализацию файла владения.
   Наличие этого ADR и пакета не означает выпуск подтверждения и не разрешает
   вызов.
7. Не выполнять в этом срезе запись подтверждения, создание файла владения,
   проверку образа, материализацию команды, потребление авторизации, создание
   процесса или Docker.

## Идентичности

```text
wiring_pr=146
wiring_head=1d4096a8086c9f9c32e1d14515ef3b702d2237ab
wiring_base=0303a1514e2875a057ef1b20293a01b36a9c6b2b
wiring_merge=2957d8f6975c88e7bdb23243e3915c7f51d4ba47
wiring_merged_at_utc=2026-07-30T14:37:25Z
wiring_focused_tests=39
wiring_targeted_tests=240
wiring_full_tests=1287
wiring_full_test_warnings=14
persistent_evidence_chain_v2_sha256=sha256:c0a6195080cec64e6104a90076366cc2bfa10a723b45a7389cd77fa1b3b11bd1
persistent_evidence_chain_v2_implementation_sha256=sha256:3671f7b12b570e7caace38dec0e023691bc1051b3cbf8e72ddfda59058369362
lease_bound_host_invoker_wiring_sha256=sha256:a064b518b960159d0fe7d9178962ecab5d2c1660deddffb3155c76db7d937655
image_repo_digest=torch2pc-layerwise-thesis@sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d
torch2pc_commit=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
invocation_count=1
```

## Граница

```text
WIRING_POST_MERGE_VERIFIED=true
PERSISTENT_EVIDENCE_CHAIN_V2_PRESENT=true
PERSISTENT_LEASE_V2_IMPLEMENTATION_PRESENT=true
DURABLE_OUTCOME_WRITER_IMPLEMENTED=true
LEASE_BOUND_HOST_INVOKER_ENFORCED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=false
FINAL_EXECUTION_ACKNOWLEDGED=false
ONE_SHOT_ENGINEERING_INVOCATION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
DURABLE_HOST_OUTCOME_PRESENT=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
IMAGE_INSPECTION_PERFORMED=false
INVOCATION_COMMAND_MATERIALIZED=false
DOCKER_RUN_PERFORMED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Последствия

Репозиторий получает машинно-проверяемый формат будущего финального
подтверждения, но не само подтверждение. Следующий допустимый этап после
слияния и повторной проверки этого пакета — отдельный срез выпуска
подтверждения. Даже выпущенное подтверждение не должно автоматически создавать
файл владения или запускать рабочую среду: материализация и вызов остаются
отдельными атомарными действиями с закрытием при ошибке.

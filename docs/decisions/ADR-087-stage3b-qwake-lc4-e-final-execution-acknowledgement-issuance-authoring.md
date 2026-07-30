# ADR-087: подготовка выпуска финального подтверждения `QW-LC4-E`

[English version](ADR-087-stage3b-qwake-lc4-e-final-execution-acknowledgement-issuance-authoring_EN.md)

- **Статус:** принят как статический контракт выпуска; подтверждение не выпущено
- **Дата:** 2026-07-30
- **Базовый коммит:** `eb20c157584efff8e9aa0418385242c7d7b26eab`

## Контекст

PR №147 зафиксировал машинно-проверяемый формат будущего операторского
подтверждения и был независимо проверен после слияния. Формат связывает точную
фразу, оператора, время, доказательную цепочку, образ, Torch2PC, каталог
результатов и одну попытку. Однако формат подтверждения ещё не определяет
безопасную долговечную выдачу файла подтверждения.

Выдача должна быть отдельной от подготовки формата, реализации записи,
материализации файла владения и запуска. Ошибка, коллизия или расхождение
идентичности не должны приводить к частично выданному подтверждению или
автоматическому разрешению выполнения.

## Решение

1. Добавить статический пакет подготовки выпуска
   `stage3b-qwake-lc4-e-final-execution-acknowledgement-issuance-authoring-v1`.
2. Сохранить точную квитанцию проверки слияния PR №147: `50` направленных,
   `251` расширенный и `1298` полных тестов при `14` предупреждениях,
   обязательные проверки CI, Ruff, `mypy`, обе сборки документации,
   идентичность Torch2PC и закрытую производственную границу.
3. Связать выпуск с точным пакетом ADR-086, его семантической и файловой
   идентичностью, реестрами исходных файлов, модулем, проверяющей программой,
   тестом и обеими версиями ADR.
4. Зафиксировать единственный будущий путь подтверждения
   `results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001.final-execution-acknowledgement.json`.
5. Требовать точную операторскую фразу, идентичность оператора и время
   подтверждения строго после слияния PR №147, а также отдельную идентичность
   выпускающего и время выпуска не раньше времени подтверждения.
6. Для будущей реализации требовать канонические байты `JSON`, атомарную
   эксклюзивную запись без перезаписи, режим `0600`, `fsync` файла и каталога,
   заранее существующий несимвольный родительский каталог, очистку временного
   файла и повторную проверку точных сохранённых байтов.
7. Ограничить выпуск одной попыткой без повтора. Даже успешная будущая выдача
   подтверждения не должна автоматически создавать файл владения, потреблять
   авторизацию, проверять образ, материализовывать команду или разрешать вызов.
8. Не выполнять в этом срезе запись подтверждения, создание файла владения,
   проверку образа, материализацию команды, создание процесса или Docker.

## Идентичности

```text
acknowledgement_authoring_pr=147
acknowledgement_authoring_head=d75a767c714da7437ceef2be78c0c5ee479d66b2
acknowledgement_authoring_base=2957d8f6975c88e7bdb23243e3915c7f51d4ba47
acknowledgement_authoring_merge=eb20c157584efff8e9aa0418385242c7d7b26eab
acknowledgement_authoring_merged_at_utc=2026-07-30T16:03:05Z
acknowledgement_authoring_focused_tests=50
acknowledgement_authoring_targeted_tests=251
acknowledgement_authoring_full_tests=1298
acknowledgement_authoring_full_test_warnings=14
acknowledgement_authoring_sha256=sha256:fb76d1c483a5ba15ca629edd6b2866eac0d497fd3569241a0c78fddbb5c50cd7
acknowledgement_relative=results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001.final-execution-acknowledgement.json
file_mode=0600
invocation_count=1
```

## Граница

```text
FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORING_POST_MERGE_VERIFIED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_AUTHORED=true
ACKNOWLEDGEMENT_ISSUANCE_CONTRACT_AUTHORED=true
ACKNOWLEDGEMENT_ISSUANCE_IMPLEMENTED=false
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

Репозиторий получает проверяемый контракт будущей выдачи, но не программу
записи и не выданное подтверждение. Следующий допустимый этап после слияния и
повторной проверки — отдельная реализация атомарной выдачи. Материализация
подтверждения и последующий файл владения остаются разными срезами.

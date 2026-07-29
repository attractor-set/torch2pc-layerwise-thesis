# ADR-075: реализация одноразового хостового исполнителя `QW-LC4-E`

- **Статус:** принят
- **Дата:** 2026-07-29
- **Область:** `QW-LC4-E`, инженерный одноразовый вызов

## Контекст

ADR-074 зафиксировал будущую хостовую границу: единственный [запуск](../glossary.md#term-run) контейнера,
но намеренно не содержал исполняющего кода. После проверенного слияния PR №135
в `main` `7f1655346bca77834d73a660c9857f1ff23b826c` требуется реализовать эту
границу без фактического вызова [рабочей среды](../glossary.md#term-runtime) в текущем срезе.

## Решение

Добавляется отдельный модуль реализации. Импорт модуля не создаёт эффектов.
Явно вызываемая функция:

1. повторно проверяет точный авторинг-контракт и отсутствие файла владения,
   результата и временного дерева;
2. дважды проверяет локальный неизменяемый образ;
3. дважды строит канонический `docker run` как кортеж `argv` и требует полное
   совпадение непосредственно перед запуском;
4. создаёт не более одного дочернего процесса через единственный `Popen` с
   `shell=False`, отдельной группой процессов и фиксированной хостовой средой;
5. пересылает `SIGINT` и `SIGTERM`, применяет терминальный тайм-аут и запрещает
   автоматический повтор после [попытки](../glossary.md#term-attempt) запуска;
6. ограничивает захват `stdout` и `stderr` одним MiB на поток и возвращает
   только результат в памяти без сохранения команды или хостовых журналов.

Хост никогда не записывает файл владения. Его атомарно захватывает только
контейнерная точка входа в том же процессе, который затем повторно проверяет
допуск и вызывает ограниченный вычислительный модуль.

## Граница текущего среза

Реализация исполнителя и точного `docker run` присутствует, но веточный допуск
выполнения остаётся закрытым. Проверяющая программа не вызывает исполняющую функцию;
модульные тесты используют только поддельный дочерний процесс. Поэтому файл
владения, потребление разрешения, [выполнение](../glossary.md#term-execution) и результаты не возникают.

```text
HOST_RUNTIME_INVOKER_CONTRACT_PRESENT=true
HOST_RUNTIME_INVOKER_IMPLEMENTATION_PRESENT=true
HOST_RUNTIME_INVOKER_PRESENT=true
HOST_RUNTIME_INVOKER_EXECUTABLE=true
HOST_DOCKER_RUN_IMPLEMENTED=true
PRELAUNCH_IMAGE_INSPECTION_COUNT=2
PRELAUNCH_MATERIALIZATION_COUNT=2
SUBPROCESS_POPEN_CALL_LIMIT=1
EXACT_ARGV_ONLY=true
SHELL_INTERPRETATION_FORBIDDEN=true
ENVIRONMENT_INHERITANCE_FORBIDDEN=true
PROCESS_GROUP_REQUIRED=true
SIGNAL_FORWARDING_REQUIRED=true
BOUNDED_OUTPUT_CAPTURE_REQUIRED=true
AUTOMATIC_RETRY_AFTER_SPAWN_FORBIDDEN=true
HOST_EXECUTION_LEASE_WRITE_FORBIDDEN=true
BRANCH_RUNTIME_EXECUTION_PERMITTED=false
EXECUTION_LEASE_MATERIALIZED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Последствия

Следующий срез может зафиксировать точную реализацию в репозитории и отдельно
подготовить единственную операторскую операцию вызова. Само слияние ADR-075 не
разрешает запуск и не изменяет одноразовое разрешение.

# ADR-129: терминальный отказ `C1 Attempt-001` и исправление идентичности научного хоста

[English version](ADR-129-stage3b-qwake-c1-attempt-001-host-identity-permission-correction_EN.md)

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-c1-attempt-001-host-identity-permission-correction-v1/correction.json -->

## Статус

Повторно авторено от проверенного после слияния `main` после системного
рефакторинга языковой проверки; семантика минимального исправления исходного
кода после терминального потребления `C1 Attempt-001` не изменена. Эта
[попытка](../glossary.md#term-attempt) не может быть повторена. Этот срез не
строит новый образ, не фиксирует новый запрос C1 и не разрешает `Attempt-002`
или новое [выполнение](../glossary.md#term-execution).

## Причина

`C1 Attempt-001` потребил научную авторизацию через точный `host-claim.json`,
после чего первая встроенная операция записи `authorization-consumption.json`
завершилась `PermissionError`.

Проверка только для чтения исключила `rootless/userns`. Хост создал каталог
вывода от `UID/GID` хоста с режимом `0775`; образ объявлял пользователя `root`,
но средство запуска применяло `--cap-drop=ALL` и не задавало `--user`.
Контейнер с `UID 0` без `CAP_DAC_OVERRIDE` попал в класс `Unix DAC` `other`,
где `0775` даёт `r-x`, но не право записи.

## Решение

1. Сохранить `--cap-drop=ALL`, `no-new-privileges`, корневую файловую систему
   только для чтения и `network=none`.
2. Не возвращать `CAP_DAC_OVERRIDE`.
3. Привязать основную идентичность контейнера к `uid:gid` хоста.
4. Добавить `GID` групп `video` и `render` как дополнительные группы для ROCm.
5. Создавать каталог вывода с режимом `0700`; до создания `host-claim.json`
   проверять `UID` владельца и его права на запись и выполнение.
6. Точный действительный `host-claim.json` нормативно означает
   `AUTHORIZATION_CONSUMED=true` даже без терминальной квитанции; будущая
   оболочка выполнения обязана отражать это.
7. Сохранить `C1 Attempt-001` и его
   [доказательные материалы](../glossary.md#term-evidence) неизменными.
8. Поскольку замороженное исходное окружение
   [времени выполнения](../glossary.md#term-runtime) изменяется, для
   `Attempt-002` требуются новый научный образ и новая цепочка запроса и
   авторизации C1.

```text
ATTEMPT001_AUTHORIZATION_CONSUMED=true
ATTEMPT001_RETRY_PERMITTED=false
ATTEMPT001_TERMINAL_FAILURE=true
CAP_DROP_ALL_PRESERVED=true
CAP_DAC_OVERRIDE_ADDED=false
CONTAINER_PRIMARY_IDENTITY_BOUND_TO_HOST_UID_GID=true
VIDEO_RENDER_SUPPLEMENTARY_GROUPS_BOUND=true
PRECLAIM_OUTPUT_OWNER_WRITE_CONTRACT=true
SUCCESSOR_RUNTIME_MANIFEST_SHA256=sha256:fbfd01ecd41cc1615acef9f0fc9b3dd390e9605ebadd9a5dc86d78a425e2ac7b
CORRECTION_SHA256=sha256:dd827f2ecb5fc983ad9d800961c34f61d443240651dc007526332fe6215d24aa
DOCKER_BUILD_INVOKED=false
DOCKER_RUN_INVOKED=false
ATTEMPT002_CREATED=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
```

# ADR-115: одноразовая авторизация хостового вызова попытки 002

- **Статус:** принят в составе единственного корректирующего PR №179
- **Дата:** 2026-08-04
- **Связанные решения:** [ADR-111](ADR-111-stage3b-qwake-lc4-e-claim-execute-order-correction.md), [ADR-112](ADR-112-stage3b-qwake-lc4-e-attempt-002-container-runtime.md), [ADR-113](ADR-113-stage3b-qwake-lc4-e-attempt-002-execution-freeze.md), [ADR-114](ADR-114-stage3b-qwake-lc4-e-attempt-002-host-invocation-chain.md)

## Контекст

Четвёртый коммит PR №179 независимо подтвердил исправленный образ, отдельную [фиксацию](../glossary.md#term-freeze) выполнения и чистую хостовую цепочку будущей попытки 002. Следующий допустимый переход — отдельная одноразовая авторизация. Она не должна создавать процесс, контейнер, владение, устойчивый исход или начинать [выполнение](../glossary.md#term-execution).

Авторизация должна быть связана с точными идентичностями ADR-113 и ADR-114. Она не разрешает научный [запуск](../glossary.md#term-run), публикацию и не делает доступным тестовый [набор данных](../glossary.md#term-dataset).

## Решение

Создаётся канонический объект `stage3b-qwake-lc4-e-attempt-002-authorization-v1`. Он:

- привязан к попытке `stage3b-qwake-lc4-runtime-validation-v1-attempt-002`;
- привязан к `freeze_sha256=sha256:09ca6e2b70fe1c7352c35d694952b4ea199e85dd816588f29454a4157b711f5c`;
- привязан к локальному оператору `dzmitry-prychyna`;
- требует точную фразу `AUTHORIZE_QWAKE_LC4_ATTEMPT_002_ONE_SHOT_ENGINEERING_INVOCATION`;
- допускает ровно одно инженерное применение;
- запрещает автоматический и слепой повтор;
- остаётся непотреблённым и не начинает попытку;
- не открывает научное выполнение, тестовый набор данных или публикацию.

Текущее вычисляемое состояние хостовой цепочки меняется с `authorization_absent` на `authorized_unconsumed`. Исторический пакет ADR-114 не переписывается семантически: его запись подготовки продолжает доказывать состояние до выдачи авторизации, а обновлённый проверяющий модуль отдельно доказывает текущее состояние после выдачи.

## Граница текущего среза

```text
ATTEMPT_002_AUTHORIZATION_EFFECTIVE=true
ATTEMPT_002_AUTHORIZATION_ISSUED=true
ATTEMPT_002_AUTHORIZATION_CONSUMED=false
ATTEMPT_002_ATTEMPT_STARTED=false
AUTHORIZATION_CONSUMPTION_PERMITTED=false
POST_COMMIT_VERIFICATION_REQUIRED_BEFORE_CONSUMPTION=true
HOST_PROCESS_SPAWNER_PRESENT=false
DOCKER_RUN_IMPLEMENTED=false
DOCKER_BUILD_INVOKED=false
DOCKER_RUN_INVOKED=false
CONTAINER_CREATED=false
ATTEMPT_002_LEASE_V1_PRESENT=false
ATTEMPT_002_LEASE_V2_PRESENT=false
ATTEMPT_002_DURABLE_OUTCOME_PRESENT=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
PR_MERGED=false
QW5_OPENED=false
```

## Проверяемые инварианты

1. Объект авторизации имеет канонический формат `JSON` и собственный SHA-256.
2. Авторизация связана с точными идентичностями фиксации, образа и хостового вызова.
3. `execution_count` равен `1`, а повтор запрещён.
4. Авторизация существует, но не потреблена; [попытка](../glossary.md#term-attempt) и [среда выполнения](../glossary.md#term-runtime) не начаты.
5. Пути результата, владений и устойчивого исхода попытки 002 отсутствуют.
6. Модули подготовки и проверки не содержат поверхности запуска процесса.
7. Терминальные [доказательные материалы](../glossary.md#term-evidence) попытки 001 остаются побайтно неизменными.

## Последствия

После независимой проверки пятого коммита может быть отдельно подготовлена одноразовая хостовая операция, которая атомарно потребляет авторизацию и вызывает уже зафиксированную командную цепочку. Этот будущий переход не входит в ADR-115. PR №179 пока не сливается; [запуск](../glossary.md#term-run) и `QW-5` остаются закрытыми.

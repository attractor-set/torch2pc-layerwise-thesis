# ADR-105: фиксация области подготовки атомарной попытки потребления авторизации финального инженерного вызова `QW-LC4-E`

[English version](ADR-105-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-scope-freeze_EN.md)

- **Статус:** принято как фиксация области; [выполнение](../glossary.md#term-execution) не начато
- **Дата:** 2026-08-03
- **Контекст:** `QW-LC4-E`
- **Предшествует:** ADR-104
- **Проверенный `main`:** `47bb24dc8fa95292be33428ba8bc7ee598c49b1e`

## Контекст

PR №172 с головой `220ce31235a28d1583f90cde5acd8f87ca5c2752`
был слит в `main` как
`47bb24dc8fa95292be33428ba8bc7ee598c49b1e` в
`2026-08-03T18:18:06Z`. Независимая проверка после слияния подтвердила
однокоммитный граф PR, двухродительский граф слияния, точную область из
17 файлов, финальные проверки головы, точные SHA-256, одиннадцать замороженных
пакетов, отдельную программу проверки авторизации, `ruff`, четыре статические
проверки и 37 направленных тестов.

Каноническая запись авторизации остаётся неизменяемым предслияльным документом
с `authorization_post_merge_verified=false` и
`final_engineering_invocation_permitted=false`. Эффективность одноразового
полномочия выводится только из точного слияния PR №172 и независимой проверки
после слияния. Поэтому текущее производное состояние имеет
`authorization_post_merge_verified=true`,
`final_engineering_invocation_permitted=true` и
`authorization_consumed=false`.

Эффективное полномочие ещё не является потреблением. [Попытка](../glossary.md#term-attempt), команда, файл
владения v2, устойчивый исход хоста и выход среды выполнения отсутствуют.

## Цель текущего среза

Текущий срез фиксирует только:

1. точные входы будущей подготовки одной попытки потребления;
2. единственные допустимые программные поверхности будущей записи попытки;
3. различие между подготовкой записи и атомарной рабочей границей;
4. предусловия точного оператора и отдельной фразы действия;
5. атомарность потребления, начала попытки и эксклюзивного создания файла
   владения v2;
6. классификацию отказов до и после атомарной границы;
7. запрет повторной попытки после потребления, создания владения или
   неопределённого исхода;
8. запрещённые эффекты текущей фиксации области;
9. критерии приёмки будущей подготовки записи попытки.

Он не создаёт схему попытки, программу проверки, тесты или запись попытки и не
потребляет авторизацию.

## Допустимые входы

Будущий срез подготовки записи попытки обязан связать без изменения:

- проверенный `main`
  `47bb24dc8fa95292be33428ba8bc7ee598c49b1e`;
- PR №172, его голову
  `220ce31235a28d1583f90cde5acd8f87ca5c2752`, коммит слияния и время
  `2026-08-03T18:18:06Z`;
- Torch2PC
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- авторизацию
  `stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1` с
  семантическим SHA-256
  `sha256:629e87c79f03cd50f4b427d66b873802a06b36efe9def502b50232a474c18014`;
- оператора `local-posix-account:dzmitry-prychyna` и отдельную фразу
  `AUTHORIZE_QWAKE_LC4_FINAL_ENGINEERING_INVOCATION_ONCE_AFTER_POST_MERGE_VERIFICATION`;
- каноническую запись допуска, репозиторную печать, неизменяемый образ и
  единственную точку `invoke_lease_bound_host_runtime`;
- корень результата
  `results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001`;
- постоянный файл владения v2
  `results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001.execution-lease-v2.json`;
- устойчивый исход хоста
  `results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001.host-outcome.json`.

Исторические авторизации не являются источником полномочия. Они допустимы
только как [доказательные материалы](../glossary.md#term-evidence) запрета
повторного использования.

## Будущие программные поверхности

Только будущему отдельному срезу подготовки записи попытки разрешается создать:

```text
src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt.py
scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt.py
tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt.py
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1/attempt.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1/SHA256SUMS
```

Схема и программа проверки должны быть чистыми: они не импортируют рабочую
точку, не вызывают Docker или дочерний процесс и не создают рабочие артефакты.
Отрицательные тесты изменяют только временные копии.

## Контракт будущей записи попытки

Будущая запись обязана:

1. иметь новый идентификатор попытки и собственный семантический SHA-256;
2. связывать точную авторизацию, оператора, фразу действия, проверенный `main`,
   допуск, образ, рабочую точку и пути рабочей границы;
3. фиксировать `consumption_attempt_prepared=true`, но сохранять
   `authorization_consumed=false`, `consumption_attempt_started=false`,
   `invocation_command_materialized=false` и отсутствие файла владения v2;
4. оставаться неэффективной как разрешение на атомарное действие до собственного
   слияния и независимой проверки после слияния;
5. запрещать оболочку, прямой Docker, прямой вызов нижнего исполнителя и
   исторической операции;
6. требовать точного оператора и точной отдельной фразы непосредственно на
   будущей рабочей границе;
7. разрешать только одну атомарную операцию: потребление авторизации, начало
   [попытки](../glossary.md#term-attempt) и эксклюзивное устойчивое создание
   файла владения v2 должны стать одним неделимым переходом до вызова рабочей
   точки;
8. разрешать отказ до атомарного перехода без потребления, начала попытки или
   создания файла владения;
9. после начала атомарного перехода запрещать любой повтор независимо от
   успеха, отказа или неопределённого исхода;
10. требовать одну устойчивую квитанцию исхода хоста для каждого терминального
    класса;
11. не разрешать `QW-5`, научную кампанию, тестовую выборку или публикацию.

Материализация будущей записи попытки является подготовкой, а не потреблением.
Потребление допустимо только отдельной будущей рабочей операцией после слияния
и независимой проверки записи попытки.

## Запрещённые эффекты текущего среза

Запрещены:

- изменение канонической записи авторизации;
- создание схемы, программы проверки, тестов или записи попытки;
- потребление авторизации или начало попытки;
- материализация команды вызова;
- создание постоянного файла владения v1 или v2;
- создание устойчивого исхода хоста;
- создание корня результата или выхода среды выполнения;
- инспекция образа, Docker, модель или дочерний процесс;
- изменение существующего замороженного пакета;
- открытие `QW-5`, `C1`, `C2`, `C3`, `R`, тестовой выборки или публикации.

## Критерии приёмки будущей подготовки записи попытки

Будущий срез принимается только если:

1. все входы проверяются по точным идентичностям и SHA-256;
2. запись попытки канонична и имеет проверяемый семантический SHA-256;
3. авторизация доказуемо проверена после слияния, эффективна и непотреблена;
4. подготовка записи не изменяет авторизацию и не начинает попытку;
5. команда, владение v2, исход хоста, корень результата и выход отсутствуют;
6. атомарная рабочая граница и классы отказов заданы однозначно;
7. повтор после потребления, владения или неопределённого исхода запрещён;
8. рабочая точка, Docker и модель не импортируются и не вызываются;
9. отрицательные тесты работают только во временных копиях;
10. `QW-5` и научные возможности остаются закрытыми.

## Машиночитаемая фиксация

```text
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-scope-freeze-v1/scope.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-scope-freeze-v1/SHA256SUMS
```

## Последовательность

```text
authorization consumption-attempt scope freeze
→ consumption-attempt record authoring
→ attempt-record merge and independent verification
→ atomic authorization consumption, attempt start, and exclusive lease v2
→ invoke_lease_bound_host_runtime
→ durable host outcome
→ sealed extension engineering report
→ QW-5 eligibility decision
```

## Машинная граница

```text
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_RECORD_LINE_COMPLETE=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=true
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_SCOPE_FROZEN=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_PRESENT=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_STARTED=false
INVOCATION_COMMAND_MATERIALIZED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
EXTENSION_ENGINEERING_REPORT_PRESENT=false
QW_LC4_E_COMPLETE=false
QW5_TRANSITION_PERMITTED=false
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-scope-freeze-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-record-authoring
```

## Последствия

Этот ADR не потребляет авторизацию и не является [запуском](../glossary.md#term-run).
Он только ограничивает будущую подготовку записи попытки точными входами,
поверхностями и атомарной семантикой. Эффективное полномочие остаётся
непотреблённым, а [локальное вычисление](../glossary.md#term-local-compute) и
все научные возможности остаются закрытыми.

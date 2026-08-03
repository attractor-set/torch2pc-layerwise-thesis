# ADR-103: фиксация области подготовки новой одноразовой авторизации финального инженерного вызова `QW-LC4-E`

[English version](ADR-103-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-authoring-scope-freeze_EN.md)

- **Статус:** принято как фиксация области; [выполнение](../glossary.md#term-execution) закрыто
- **Дата:** 2026-08-03
- **Контекст:** `QW-LC4-E`
- **Предшествует:** ADR-102
- **Проверенный `main`:** `a5b96edb1f82485561e0f52d6a98432d55ae8609`

## Контекст

PR №170 с головой `6201997a71428bdb873d95d76c5b0882be532b2a`
был слит в `main` как
`a5b96edb1f82485561e0f52d6a98432d55ae8609` в
`2026-08-03T16:16:32Z`. Независимая проверка после слияния подтвердила
однокоммитный граф PR, двухродительский граф слияния, точную область из
14 файлов, успешные проверки финальной головы, `ruff`, четыре статические
проверки и 27 направленных тестов.

Двухфайловая репозиторная печать допуска остаётся неизменяемым
предслияльным свидетельством с
`repository_seal_complete=false`. Её завершённость выводится из точного
слияния PR №170 и независимой проверки после слияния. Это разрешает только
отдельную фиксацию области будущей подготовки новой авторизации. Авторизация,
фраза оператора, команда вызова и рабочие артефакты по-прежнему отсутствуют.

## Цель текущего среза

Текущий срез фиксирует только:

1. точные репозиторные и доказательные входы будущей авторизации;
2. единственные допустимые программные поверхности будущей подготовки;
3. обязательные поля и семантику новой одноразовой записи;
4. её отличие от всех исторических разрешений;
5. порядок выпуска, проверки после слияния, потребления и единственной
   [попытки](../glossary.md#term-attempt);
6. запрещённые эффекты текущей фиксации области;
7. критерии приёмки будущего среза подготовки записи.

Он не создаёт схему авторизации, программу проверки, тесты, запись
авторизации или фразу оператора.

## Допустимые входы

Будущий срез подготовки авторизации обязан связать без изменения:

- проверенный `main`
  `a5b96edb1f82485561e0f52d6a98432d55ae8609`;
- PR №170, его голову
  `6201997a71428bdb873d95d76c5b0882be532b2a`, коммит слияния и время
  `2026-08-03T16:16:32Z`;
- Torch2PC
  `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- неизменяемую репозиторную печать допуска и её точный SHA-256;
- каноническую запись допуска, её внутренний
  `admission_sha256` и реестры SHA-256;
- неизменяемый образ
  `torch2pc-layerwise-thesis@sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d`;
- единственную перспективную точку
  `invoke_lease_bound_host_runtime`;
- корень результата, постоянный файл владения v2 и устойчивый исход хоста,
  уже связанные записью допуска.

Историческая инженерная авторизация `QW-LC4-F` и потреблённая авторизация
материализации финального подтверждения могут использоваться только как
[доказательные материалы](../glossary.md#term-evidence) запрета повторного
использования. Они не являются источником полномочия.

## Будущие программные поверхности

Только будущему отдельному срезу подготовки записи разрешается создать:

```text
src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_authorization.py
scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_authorization.py
tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_authorization.py
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/authorization.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/SHA256SUMS
```

Схема и программа проверки должны оставаться чистыми: они не импортируют
рабочую точку, не вызывают Docker или дочерний процесс и не создают файлы
рабочей среды. Отрицательные тесты изменяют только временные копии.

## Контракт будущей записи

Будущая запись обязана:

1. иметь новый идентификатор и собственный семантический SHA-256;
2. фиксировать точного оператора и отдельную фразу действия;
3. связывать проверенный `main`, репозиторную печать, запись допуска,
   Torch2PC, образ, точку вызова и все пути рабочей границы;
4. разрешать не более одной [попытки](../glossary.md#term-attempt);
5. запрещать оболочку, прямой Docker, прямой вызов нижнего исполнителя и
   исторической операции;
6. запрещать автоматический, слепой и ручной повтор после потребления,
   создания файла владения v2 или неопределённого исхода;
7. требовать атомарного потребления с началом попытки и эксклюзивным созданием
   постоянного файла владения v2;
8. требовать одну устойчивую квитанцию исхода хоста для каждого терминального
   класса;
9. оставаться неэффективной до собственного слияния и независимой проверки
   после слияния;
10. не разрешать `QW-5`, научную кампанию, тестовую выборку или публикацию.

Материализация будущей записи может зафиксировать
`authorization_issued=true`, но до проверки после слияния обязана сохранять
`authorization_post_merge_verified=false`,
`final_engineering_invocation_permitted=false` и
`authorization_consumed=false`.

## Запрещённые эффекты текущего среза

Запрещены:

- создание схемы, программы проверки, тестов или записи авторизации;
- выпуск или потребление авторизации;
- резервирование фразы оператора;
- материализация команды вызова;
- создание постоянного файла владения v1 или v2;
- создание устойчивого исхода хоста;
- создание корня результата или выхода среды выполнения;
- инспекция образа, Docker, модель или дочерний процесс;
- изменение существующего замороженного пакета;
- открытие `QW-5`, `C1`, `C2`, `C3`, `R`, тестовой выборки или публикации.

## Критерии приёмки будущей подготовки авторизации

Будущий срез принимается только если:

1. все разрешённые входы проверяются по точным идентичностям;
2. новая запись канонична и имеет проверяемый семантический SHA-256;
3. идентификатор, оператор и фраза действия однозначны;
4. исторические разрешения явно непригодны для повторного использования;
5. запись допускает ровно одну будущую попытку;
6. запись выпущена, но неэффективна до независимой проверки после слияния;
7. рабочая точка, Docker и модель не импортируются и не вызываются;
8. файл владения, исход хоста, корень результата и выход отсутствуют;
9. отрицательные тесты работают только во временных копиях;
10. `QW-5` и научные возможности остаются закрытыми.

## Машиночитаемая фиксация

```text
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-authoring-scope-freeze-v1/scope.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-authoring-scope-freeze-v1/SHA256SUMS
```

## Последовательность

```text
authorization-authoring scope freeze
→ authorization record authoring
→ authorization merge and independent verification
→ atomic authorization consumption, attempt start, and lease v2
→ invoke_lease_bound_host_runtime
→ durable host outcome
→ sealed extension engineering report
→ QW-5 eligibility decision
```

## Машинная граница

```text
FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_SEAL_COMPLETE=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORING_SCOPE_FROZEN=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_RECORD_PRESENT=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=false
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
OPERATOR_PHRASE_RESERVED=false
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
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-authoring-scope-freeze-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-record-authoring
```

## Последствия

Этот ADR не является авторизацией и не разрешает [запуск](../glossary.md#term-run).
Он только ограничивает будущую подготовку новой записи точными входами,
поверхностями и одноразовой семантикой. [Локальное вычисление](../glossary.md#term-local-compute)
и все научные возможности остаются закрытыми.

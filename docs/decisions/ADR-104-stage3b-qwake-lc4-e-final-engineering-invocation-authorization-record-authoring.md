# ADR-104: подготовка канонической одноразовой авторизации финального инженерного вызова `QW-LC4-E`

[English version](ADR-104-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-record-authoring_EN.md)

- **Статус:** принято как подготовка записи; [выполнение](../glossary.md#term-execution) закрыто
- **Дата:** 2026-08-03
- **Контекст:** `QW-LC4-E`
- **Предшествует:** ADR-103
- **Проверенный `main`:** `61f190db2fbd4bf0ee8a58cac8b6841fbecc6cdd`

## Контекст

PR №171 с головой `6093a18156036d8aa470c88844b0580cd3926c4e` был слит в `main` как
`61f190db2fbd4bf0ee8a58cac8b6841fbecc6cdd` в `2026-08-03T17:17:04Z`. Независимая проверка после слияния
зафиксировала однокоммитный граф PR, двухродительский граф слияния, точную
область из 13 файлов, успешные проверки финальной головы, `ruff`, четыре
статические проверки и 27 направленных тестов.

Неизменяемая фиксация области ADR-103 завершена сочетанием собственного
слияния и независимой проверки после слияния. Поэтому разрешена подготовка
новой записи авторизации. Эта подготовка не открывает [запуск](../glossary.md#term-run):
запись остаётся неэффективной до собственного слияния и независимой проверки
после слияния.

## Решение

Создать отдельную каноническую запись:

```text
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/authorization.json
```

Запись имеет идентификатор:

```text
stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1
```

и связывает:

- проверенный `main` `61f190db2fbd4bf0ee8a58cac8b6841fbecc6cdd`;
- PR №171, его голову `6093a18156036d8aa470c88844b0580cd3926c4e` и время `2026-08-03T17:17:04Z`;
- Torch2PC `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`;
- неизменяемую фиксацию области ADR-103;
- репозиторную печать допуска и каноническую запись допуска;
- неизменяемый образ
  `torch2pc-layerwise-thesis@sha256:7da92b8f77f6dc37d42db832c5613ef6149dc488adc5b66465faa33e48ca021d`;
- единственную перспективную точку `invoke_lease_bound_host_runtime`;
- корень результата, постоянный файл владения v2 и устойчивый исход хоста.

## Оператор и отдельная фраза действия

Запись связывает точного оператора:

```text
identity_kind=local-posix-account
identity=dzmitry-prychyna
```

Отдельная фраза действия:

```text
AUTHORIZE_QWAKE_LC4_FINAL_ENGINEERING_INVOCATION_ONCE_AFTER_POST_MERGE_VERIFICATION
```

Фраза зарезервирована только этой записью. Она не является командой и не
может использоваться до независимой проверки будущего слияния.

## Одноразовый контракт

Запись допускает не более одной будущей [попытки](../glossary.md#term-attempt)
и требует:

1. отдельной проверки после слияния до возникновения эффективного полномочия;
2. атомарного потребления авторизации с началом попытки и эксклюзивным
   созданием постоянного файла владения v2;
3. устойчивого исхода хоста для каждого терминального класса;
4. запрета повтора после потребления, создания файла владения или
   неопределённого исхода;
5. запрета оболочки, прямого Docker, прямого нижнего исполнителя и
   исторической операции;
6. запрета повторного использования инженерной и подтверждающей
   авторизаций;
7. сохранения закрытыми `QW-5`, тестовой выборки и публикации.

## Программные поверхности

Текущий срез создаёт:

```text
src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_authorization.py
scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_authorization.py
tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_authorization.py
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/authorization.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/SHA256SUMS
```

Схема и программа проверки не импортируют рабочую точку, не вызывают Docker,
не запускают дочерний процесс и не создают рабочие артефакты. Отрицательные
тесты изменяют только временные копии.

## Состояние выпуска

Запись фиксирует:

```text
authorization_issued=true
authorization_post_merge_verified=false
final_engineering_invocation_permitted=false
authorization_consumed=false
```

Следовательно, выпуск записи ещё не является правом вызова.

## Запрещённые эффекты

Текущий срез не:

- материализует команду вызова;
- потребляет авторизацию;
- создаёт постоянный файл владения v1 или v2;
- создаёт устойчивый исход хоста;
- создаёт корень результата или выход среды выполнения;
- инспектирует образ;
- вызывает Docker, модель, рабочую точку или дочерний процесс;
- открывает `QW-5`, научную кампанию, тестовую выборку или публикацию;
- изменяет существующие замороженные пакеты.

## Машиночитаемый пакет

```text
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/authorization.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1/SHA256SUMS
```

Внутренний `authorization_sha256` вычисляется по каноническому объекту без
самого поля хэша. `SHA256SUMS` связывает запись и реестр источников.

## Машинная граница

```text
FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_SEAL_COMPLETE=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORING_SCOPE_FREEZE_COMPLETE=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_RECORD_PRESENT=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=false
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
OPERATOR_PHRASE_RESERVED=true
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
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-record-authoring-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-scope-freeze
```

## Последовательность

```text
authorization record authoring
→ merge and independent post-merge verification
→ authorization consumption/attempt scope freeze
→ atomic consumption, attempt start, and lease v2
→ invoke_lease_bound_host_runtime
→ durable host outcome
→ sealed extension engineering report
→ QW-5 eligibility decision
```

## Последствия

Новая запись отличается от исторических разрешений, канонична и связана с
точным оператором. До будущей проверки после слияния она не разрешает
[выполнение](../glossary.md#term-execution), [локальное вычисление](../glossary.md#term-local-compute)
или научную кампанию.

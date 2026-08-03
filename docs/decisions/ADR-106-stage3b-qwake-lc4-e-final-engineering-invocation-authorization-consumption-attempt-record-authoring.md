# ADR-106: подготовка записи попытки потребления авторизации финального инженерного вызова `QW-LC4-E`

[English version](ADR-106-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-record-authoring_EN.md)

- **Статус:** принято как неисполняющая подготовка записи [попытки](../glossary.md#term-attempt)
- **Дата:** 2026-08-03
- **Контекст:** `QW-LC4-E`
- **Предшествует:** ADR-105
- **Проверенный `main`:** `28b4627436244893195231f55f2d0d5fb2d1062e`

## Контекст

PR №173 с головой `17af7d6f4473af846f2d293192082074cad99cf2` был слит в `main` как
`28b4627436244893195231f55f2d0d5fb2d1062e` в `2026-08-03T19:38:32Z`. Независимая проверка после слияния
подтвердила однокоммитный граф PR, двухродительский граф слияния, точную область
из 13 файлов, финальные проверки головы, точные SHA-256, двенадцать замороженных
пакетов, программу проверки авторизации, `ruff`, четыре статические проверки и
37 направленных тестов.

Фиксация области ADR-105 теперь завершена производным фактом
`consumption_attempt_scope_freeze_post_merge_verified=true`. Одноразовая
авторизация остаётся эффективной и непотреблённой. Запись попытки, команда,
файл владения v2, устойчивый исход хоста и выход среды выполнения отсутствуют.

## Решение

Материализовать отдельную каноническую запись
`stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1`. Запись отмечает только
`authorization_consumption_attempt_prepared=true`. Она не является
[выполнением](../glossary.md#term-execution), не потребляет авторизацию и не
начинает попытку.

Запись связывает:

- проверенный `main` `28b4627436244893195231f55f2d0d5fb2d1062e`;
- PR №173, его голову, точный коммит и время слияния;
- замороженную область ADR-105 и её точные SHA-256;
- авторизацию `stage3b-qwake-lc4-e-final-engineering-invocation-authorization-v1` с семантическим SHA-256 `sha256:629e87c79f03cd50f4b427d66b873802a06b36efe9def502b50232a474c18014`;
- оператора `local-posix-account:dzmitry-prychyna` и отдельную фразу `AUTHORIZE_QWAKE_LC4_FINAL_ENGINEERING_INVOCATION_ONCE_AFTER_POST_MERGE_VERIFICATION`;
- единственную точку `invoke_lease_bound_host_runtime`;
- корень результата, файлы владения v1/v2 и устойчивый исход хоста;
- атомарную будущую границу потребления, начала попытки и эксклюзивного
  устойчивого создания владения v2.

## Состояние подготовленной записи

```text
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_AUTHORED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_STARTED=false
```

`prepared=true` означает наличие проверяемого намерения и точных входов. Оно не
означает резервирование, владение, [запуск](../glossary.md#term-run) или потребление полномочия.

## Будущая атомарная граница

После собственного слияния записи и независимой проверки отдельный будущий
срез должен сначала зафиксировать область рабочей операции. Только затем одна
неделимая операция может:

1. потребить авторизацию;
2. отметить начало единственной попытки;
3. эксклюзивно и устойчиво создать файл владения v2;
4. проверить точные сохранённые байты владения;
5. вызвать `invoke_lease_bound_host_runtime`.

Отказ до атомарного перехода не потребляет авторизацию, не начинает попытку и
не создаёт владение. После начала перехода повтор запрещён при успехе, отказе
или неопределённом исходе. Каждый терминальный класс требует устойчивой
квитанции исхода хоста.

## Неизменяемые запреты текущего среза

Текущий срез не:

- изменяет `scope.json` ADR-105 или `authorization.json` ADR-104;
- потребляет авторизацию или начинает попытку;
- материализует команду вызова;
- создаёт файл владения v1/v2, корень результата или устойчивый исход;
- импортирует или вызывает рабочую точку, Docker, модель или дочерний процесс;
- открывает `QW-5`, тестовую выборку, научную кампанию или публикацию.

Отрицательные тесты изменяют только временные копии исходных пакетов. Это
сохраняет замороженные [доказательные материалы](../glossary.md#term-evidence)
неизменными.

## Машиночитаемые поверхности

```text
src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt.py
scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt.py
tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt.py
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1/attempt.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-v1/SHA256SUMS
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
AUTHORIZATION_CONSUMPTION_ATTEMPT_SCOPE_FREEZE_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_AUTHORING_ADMISSIBLE=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_AUTHORED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
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
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-record-authoring-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-scope-freeze
```

## Последствия

Запись попытки становится канонической и подготовленной, но остаётся
неэффективной для атомарного действия до собственного слияния и независимой
проверки. Авторизация остаётся непотреблённой; [локальное вычисление](../glossary.md#term-local-compute)
и научные возможности закрыты.

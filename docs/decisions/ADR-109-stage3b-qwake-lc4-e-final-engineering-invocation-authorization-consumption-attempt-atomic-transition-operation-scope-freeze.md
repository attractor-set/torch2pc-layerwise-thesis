# ADR-109: фиксация области эксплуатации атомарного перехода потребления авторизации `QW-LC4-E`

[English version](ADR-109-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-scope-freeze_EN.md)

- **Статус:** принято как неисполняющая фиксация области будущей операции
- **Дата:** 2026-08-04
- **Контекст:** `QW-LC4-E`

## Контекст

[ADR-108](ADR-108-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-authoring.md) реализовал точку входа `execute_final_engineering_invocation_atomic_transition_once`, но оставил её производственный вызов закрытым. После слияния PR №176 как `3a0cf60e37de80cffdbc397616db6ad437a734e0` и независимой проверки переход считается проверенным после слияния. Разрешение остаётся непотреблённым, [попытка](../glossary.md#term-attempt) — неначатой, а конечная аренда v2 отсутствует.

## Решение

Зафиксировать точную область будущей операторской операции, не выполняя её. Будущая подготовка операции должна строить `AtomicTransitionAdmission` только со следующими значениями:

```text
transition_post_merge_verified=true
implementation_merge_commit=3a0cf60e37de80cffdbc397616db6ad437a734e0
operator_identity_kind=local-posix-account
operator_identity=dzmitry-prychyna
authorization_action_phrase=AUTHORIZE_QWAKE_LC4_FINAL_ENGINEERING_INVOCATION_ONCE_AFTER_POST_MERGE_VERIFICATION
persistent_lease_acknowledgement=CLAIM_QWAKE_LC4_ONE_SHOT_PERSISTENT_EVIDENCE_CHAIN_V2
```

После построения допуска разрешён не более чем один будущий производственный вызов существующей точки входа. Единственным дополнительным параметром является `claimed_at_utc`: он должен быть получен один раз после допуска операции, иметь точный формат `UTC` с суффиксом `Z` и не может повторно использоваться после фиксации или неизвестного исхода.

## Порядок предварительной проверки

1. доказать собственную проверку после слияния для точного будущего пакета операции;
2. проверить чистое точное состояние репозитория и закреплённый `Torch2PC`;
3. проверить неизменяемые пакеты перехода, разрешения и попытки;
4. подтвердить эффективное непотреблённое разрешение и подготовленную неначатую попытку;
5. проверить личность оператора и две различные обязательные фразы;
6. доказать отсутствие каталога результата, владения v1, владения v2 и устойчивого исхода;
7. получить одно значение `claimed_at_utc`;
8. построить точный `AtomicTransitionAdmission`;
9. вызвать точку атомарного перехода не более одного раза.

## Граница эффекта

Текущий ADR создаёт только `scope.json` и его реестр. Он не создаёт модуль операции, проверяющий модуль, тесты или запись операции. Он не вызывает атомарный переход или механизм записи и не создаёт владение v2.

Будущая операция фиксирует только атомарный переход. `invoke_lease_bound_host_runtime` остаётся после неё и вне её. Создание команды оболочки, прямой Docker-вызов и автоматический повтор запрещены.

## Состояния

- до операции разрешение непотреблено, попытка не начата и владение v2 отсутствует;
- отказ до точки устойчивой фиксации при доказанном отсутствии конечного файла не создаёт подтверждённого эффекта, но не разрешает автоматический повтор;
- точное владение v2 означает одновременно потреблённое разрешение, начатую попытку и совершившийся атомарный эффект; повтор запрещён;
- неточный или неоднозначный конечный объект означает `unknown_fail_closed`: [запуск](../glossary.md#term-run) среды выполнения и повтор запрещены;
- рабочее [выполнение](../glossary.md#term-execution) среды исполнения не начинается внутри атомарной операции.

## Будущие поверхности подготовки операции

```text
src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition_operation.py
scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition_operation.py
tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition_operation.py
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-v1/operation.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-v1/SHA256SUMS
```

Текущий срез этих поверхностей не создаёт.

## Машинная граница

```text
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_POST_MERGE_VERIFIED=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=true
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_FREEZE_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_AUTHORED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_FREEZE_ADMISSIBLE=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_FROZEN=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_SCOPE_FREEZE_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_AUTHORING_ADMISSIBLE=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_OPERATION_AUTHORED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_COMMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_STARTED=false
INVOCATION_COMMAND_MATERIALIZED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
QW5_TRANSITION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-scope-freeze-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-authoring
```

## Последствия

После слияния ADR-109 и независимой проверки допускается только отдельная неисполняющая подготовка операторской операции. Сам атомарный эффект, среда исполнения, `QW-5`, тестовая выборка и публикация остаются закрытыми.

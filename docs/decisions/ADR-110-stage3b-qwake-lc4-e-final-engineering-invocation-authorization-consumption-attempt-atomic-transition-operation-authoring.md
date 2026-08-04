# ADR-110: объединённая подготовка одноразовой операции атомарного перехода `QW-LC4-E`

[English version](ADR-110-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-authoring_EN.md)

- **Статус:** принято как неисполняющая подготовка операции и её допуска
- **Дата:** 2026-08-04
- **Контекст:** `QW-LC4-E`

## Контекст

[ADR-109](ADR-109-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-operation-scope-freeze.md) зафиксировал точную область будущей операторской операции. PR №177 слит как `e33448d10ced2bffd1e48449e6da46b2de938141` с головой `b3aa449c138285ce065a3a2920fac19f15134207` в `2026-08-04T02:14:33Z` и независимо проверен. Разрешение остаётся непотреблённым, [попытка](../glossary.md#term-attempt) — неначатой, аренда v2 отсутствует.

Чтобы не продолжать чрезмерное дробление процесса, подготовка модуля операции, неизменяемой записи, контракта допуска, проверяющего модуля и тестов объединяется в один неисполняющий PR. Отдельные PR реализации и допуска после него не требуются.

## Решение

Добавить точку входа:

```text
execute_final_engineering_invocation_atomic_transition_operation_once
```

Она принимает `project_root` и `AtomicTransitionOperationAdmission`. Допуск обязан доказать:

```text
operation_post_merge_verified=true
operation_implementation_merge_commit=<точный будущий коммит слияния ADR-110>
repository_head=<тот же commit>
worktree_and_index_clean=true
torch2pc_head=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
operator_identity_kind=local-posix-account
operator_identity=dzmitry-prychyna
authorization_action_phrase=AUTHORIZE_QWAKE_LC4_FINAL_ENGINEERING_INVOCATION_ONCE_AFTER_POST_MERGE_VERIFICATION
persistent_lease_acknowledgement=CLAIM_QWAKE_LC4_ONE_SHOT_PERSISTENT_EVIDENCE_CHAIN_V2
```

После полного допуска операторская обёртка:

1. проверяет неизменяемый пакет ADR-110 и связанные исходные идентичности;
2. проверяет неизменяемую область ADR-109 и переход ADR-108;
3. классифицирует уже существующие конечные объекты до получения времени;
4. получает ровно одно значение `claimed_at_utc` в формате `UTC` с `Z`;
5. строит точный `AtomicTransitionAdmission` с `implementation_merge_commit=3a0cf60e37de80cffdbc397616db6ad437a734e0`;
6. делегирует ровно один вызов `execute_final_engineering_invocation_atomic_transition_once`;
7. возвращает подтверждённое состояние без запуска среды исполнения.

## Объединённый контракт допуска

Контракт допуска находится в том же модуле и неизменяемой записи, что и операторская обёртка. Независимая проверка будущего слияния должна подставить точный коммит слияния ADR-110 одновременно как `operation_implementation_merge_commit` и `repository_head`. Значение `e33448d10ced2bffd1e48449e6da46b2de938141` не допускается как терминальная идентичность реализации операции.

Булево утверждение о чистоте рабочего дерева не заменяет внешнюю проверку: производственная процедура обязана самостоятельно доказать чистый `HEAD`, индекс, рабочее дерево и закреплённый `Torch2PC`, а затем построить объект допуска с уже проверенными значениями.

## Одноразовость и состояния

- точная аренда v2, существующая до вызова операторской обёртки, означает уже совершившийся атомарный переход; часы не читаются, делегирование не выполняется, повтор запрещён;
- неточная, символическая, неверно защищённая или неоднозначная аренда v2 означает `unknown_fail_closed`; часы не читаются, [запуск](../glossary.md#term-run) [среды выполнения](../glossary.md#term-runtime) и повтор запрещены;
- существующий каталог результата, аренда v1 или устойчивый исход до операции означает неоднозначную границу и закрывает операцию;
- отказ до устойчивой фиксации при доказанном отсутствии конечного объекта не разрешает автоматический повтор;
- успешный вызов создаёт точную аренду v2, из которой выводятся потребление разрешения, начало попытки и фиксация атомарного действия;
- `invoke_lease_bound_host_runtime` остаётся отдельным последующим действием и не вызывается операторской обёрткой.

## Граница текущего PR

Текущий PR создаёт модуль, проверяющий модуль, тесты, `operation.json`, `source-SHA256SUMS`, `SHA256SUMS` и двуязычную документацию. Он не вызывает производственную операцию, переход или механизм записи. Эффектные тесты выполняются только во временных копиях репозитория.

```text
AUTHORIZATION_CONSUMED=false
CONSUMPTION_ATTEMPT_STARTED=false
ATOMIC_TRANSITION_OPERATION_SCOPE_FREEZE_POST_MERGE_VERIFIED=true
ATOMIC_TRANSITION_OPERATION_AUTHORING_ADMISSIBLE=true
ATOMIC_TRANSITION_OPERATION_AUTHORED=true
ATOMIC_TRANSITION_OPERATION_MODULE_CREATED=true
ATOMIC_TRANSITION_OPERATION_VERIFIER_CREATED=true
ATOMIC_TRANSITION_OPERATION_TESTS_CREATED=true
ATOMIC_TRANSITION_OPERATION_RECORD_CREATED=true
COMBINED_OPERATION_ADMISSION_CONTRACT_CREATED=true
ATOMIC_TRANSITION_OPERATION_POST_MERGE_VERIFIED=false
CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
CONSUMPTION_ATTEMPT_ATOMIC_ACTION_COMMITTED=false
INVOCATION_COMMAND_MATERIALIZED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
QW5_TRANSITION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
```

## Последствия

После слияния и независимой проверки ADR-110 отдельный PR допуска не требуется. Следующим допустимым действием становится одна внешняя, явно запущенная, закрытая при ошибке операция атомарного перехода. Она всё ещё не включает запуск среды выполнения: после устойчивой фиксации аренды v2 потребуется отдельное решение о фактическом вызове привязанного к аренде исполнителя.

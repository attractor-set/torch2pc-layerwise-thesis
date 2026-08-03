# ADR-107: фиксация области атомарного перехода потребления авторизации финального инженерного вызова `QW-LC4-E`

[English version](ADR-107-stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-scope-freeze_EN.md)

- **Статус:** принято как неисполняющая фиксация области атомарного перехода
- **Дата:** 2026-08-03
- **Контекст:** `QW-LC4-E`
- **Предшествует:** ADR-106
- **Проверенный `main`:** `5890c755fcf5aa1ae6651f3b592705457b9a9b91`

## Контекст

PR №174 с головой `bc153fb14eb73b18353739cacb5def31a8f4c70a` был слит в `main` как `5890c755fcf5aa1ae6651f3b592705457b9a9b91` в
`2026-08-03T21:20:24Z`. Независимая проверка после слияния подтвердила точный
однокоммитный граф, двухродительский граф слияния, область из 17 файлов,
финальные проверки головы, точные SHA-256, тринадцать замороженных пакетов,
обе программы проверки, `ruff`, четыре статические проверки и 47 направленных
тестов.

Подготовленная запись [попытки](../glossary.md#term-attempt) теперь проверена после слияния. Авторизация
остаётся эффективной и непотреблённой, [попытка](../glossary.md#term-attempt) подготовлена, но не начата.
Рабочая операция всё ещё не имеет права потребить авторизацию, создать файл
владения v2 или вызвать [среду выполнения](../glossary.md#term-runtime).

## Решение

Зафиксировать точную неисполняющую область будущего атомарного перехода. Три
логических эффекта — потребление авторизации, начало единственной попытки и
создание устойчивого владения v2 — не записываются в три изменяемых объекта.
Единственной точкой устойчивой фиксации является атомарное неперезаписывающее создание
полностью подготовленного канонического файла владения v2:

```text
results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001.execution-lease-v2.json
```

Состояния потреблённой авторизации и начатой попытки
являются производными от наличия этого файла как обычного файла режима `0600`
с точными ожидаемыми байтами и валидной семантикой владения v2. Неизменяемые
`authorization.json`, `attempt.json` и предшествующие `scope.json` не
перезаписываются.

## Точный протокол устойчивой фиксации

Будущая реализация обязана использовать уже проверенный механизм
`persist_persistent_execution_lease_v2`:

1. повторно проверить точные идентичности авторизации, попытки, цепочки
   доказательных материалов и среды выполнения, личность оператора и отдельную
   фразу авторизации;
2. построить канонический `PersistentExecutionLeaseV2` в памяти;
3. создать временный обычный файл в том же каталоге с `O_CREAT|O_EXCL` и
   режимом `0600`;
4. полностью записать канонические байты и выполнить `fsync` временного файла;
5. выполнить неперезаписывающий `hard link` временного индексного узла в точный финальный
   путь;
6. выполнить `fsync` родительского каталога;
7. повторно проверить точные байты, тип файла и режим финального объекта.

Успешное создание финальной жёсткой ссылки является единственной точкой устойчивой фиксации.
До неё авторизация непотреблена, попытка не начата и владение v2 отсутствует.
После неё все три логических эффекта считаются совершившимися, повтор запрещён,
даже если процесс завершился до вызова среды выполнения или до записи терминального
исхода.

## Раздельные подтверждения оператора

Фраза новой авторизации:

```text
AUTHORIZE_QWAKE_LC4_FINAL_ENGINEERING_INVOCATION_ONCE_AFTER_POST_MERGE_VERIFICATION
```

и историческое подтверждение владения v2:

```text
CLAIM_QWAKE_LC4_ONE_SHOT_PERSISTENT_EVIDENCE_CHAIN_V2
```

являются различными обязательными значениями. Будущая операция должна
проверить первое до устойчивой фиксации и построить владение с точным вторым значением. Ни
одно из них не заменяет другое.

## Состояния отказа и восстановления

- отказ до создания финальной жёсткой ссылки не потребляет авторизацию и допускает новую
  попытку только если финальный путь доказуемо отсутствует;
- точный финальный файл означает совершившийся переход и запрещает повтор;
- неточный, символический, неполный или неоднозначный финальный объект означает
  неизвестное состояние: среда выполнения закрыта, повтор запрещён;
- сбой после устойчивой фиксации, но до среды выполнения означает потреблённую авторизацию и начатую
  попытку при ещё не начатом рабочем [выполнении](../glossary.md#term-execution);
- отсутствие устойчивого исхода после фиксации классифицируется как неизвестный
  терминальный исход и не разрешает повторный вызов;
- отдельное восстановление может только классифицировать и материализовать
  исход, но не вызывать среду выполнения повторно.

Поддержка жёстких ссылок без замены и устойчивого `fsync` каталога является
обязательной. Неподдерживаемая или неоднозначная файловая система закрывает
операцию.

## Граница среды выполнения

`invoke_lease_bound_host_runtime` расположен после атомарной устойчивой фиксации и не входит
в него. Перед вызовом программа обязана проверить точные сохранённые байты
владения v2. Команда оболочки не материализуется; прямые Docker-вызовы,
исторические операции и нижележащий исполнитель хоста запрещены.

## Будущие программные поверхности

```text
src/torch2pc_thesis/stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition.py
scripts/verify_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition.py
tests/unit/test_stage3b_qwake_lc4_final_engineering_invocation_authorization_consumption_attempt_atomic_transition.py
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-v1/transition.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-v1/SHA256SUMS
```

Текущий срез этих поверхностей не создаёт и не вызывает.

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
AUTHORIZATION_CONSUMPTION_ATTEMPT_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_PREPARED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_POST_MERGE_VERIFIED=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_FROZEN=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_RECORD_PRESENT=true
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_SCOPE_FREEZE_POST_MERGE_VERIFIED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_AUTHORING_ADMISSIBLE=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_TRANSITION_AUTHORED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_PERMITTED=false
AUTHORIZATION_CONSUMPTION_ATTEMPT_ATOMIC_ACTION_COMMITTED=false
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
NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-scope-freeze-commit
POST_MERGE_NEXT_SLICE=QW-LC4-E-final-engineering-invocation-authorization-consumption-attempt-atomic-transition-authoring
```

## Последствия

Атомарность сводится к единственному устойчивому объекту фиксации, совместимому с
существующим привязанным к владению исполнителем хоста. Текущий ADR только фиксирует контракт.
Авторизация остаётся непотреблённой, попытка — неначатой, а `QW-5`, научное
[выполнение](../glossary.md#term-execution), тестовая выборка и публикация остаются закрытыми.

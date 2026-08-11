# ADR-122: успешное завершение `QW-LC4-E` и переход к `QW-5`

<!-- LANG-SOURCE: ../../experiments/frozen/stage3b-qwake-lc4-e-attempt-005-success-transition-v1/receipt.json -->

Нормативные термины:
[попытка](../glossary.md#term-attempt),
[выполнение](../glossary.md#term-execution),
[запуск](../glossary.md#term-run),
[среда выполнения](../glossary.md#term-runtime),
[доказательные материалы](../glossary.md#term-evidence),
[фиксация](../glossary.md#term-freeze),
[доступ к тестовому набору данных](../glossary.md#term-test-dataset-access) и
[набор данных](../glossary.md#term-dataset).

## Статус

Принято как переход после успешной инженерной проверки. Этот срез не выполняет
`QW-5` и не создаёт научный образ.

## Контекст

Попытка 005 была выполнена один раз из точного дерева
`170503e1f1be147be13c90f43c1012e8bb291b18` после слияния ADR-121 в `main`
`7168d6ebf3fbc27f5b85e1e44a7e8252f28038b0`. Внешний запуск создал один
дочерний процесс, завершился с `return_code=0`, не истёк по тайм-ауту и не
выполнял автоматический повтор. Одноразовое разрешение было потреблено, а
терминальный выход среды выполнения присутствует.

Запечатанный инженерный отчёт имеет статус
`engineering_matrix_completed_validation_passed`. В нём сохранены 168
разрешённых измерительных ячеек, 28 резервных проб и 14 парных агрегатов.
Одновременно прошли проверки ответа, состояния генераторов случайных чисел,
резервного пути, полноты пар и эффекта порядка. Канал CPU имеет `7/7`
прошедших агрегатов, канал ROCm — `7/7`; нарушений проверки эффекта порядка нет.

Это удовлетворяет ранее зафиксированной границе `QW-LC4-E report -> QW-5`.
Результат остаётся только инженерными доказательными материалами: научное
выполнение, доступ к тестовому набору данных и публикация этим переходом не
выполняются и не открываются.

## Решение

1. Считать попытку 005 терминальной успешной инженерной проверкой; её повтор
   запрещён и не требуется.
2. Материализовать неизменяемую квитанцию перехода
   `stage3b-qwake-lc4-e-attempt-005-success-transition-v1`, связывающую точные
   идентичности исходного кода, образа, фиксации выполнения, разрешения,
   команды хоста, владения, исхода хоста, отчёта и квитанций выполнения.
3. Зафиксировать завершение `QW-LC4-E`: `QW_LC4_E_COMPLETE=true`.
4. Разрешить следующий заранее зарегистрированный переход к `QW-5` и открыть
   только границу фиксации научного образа:
   `QW5_TRANSITION_PERMITTED=true` и
   `QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=true`.
5. Не материализовывать научный образ в этом срезе:
   `QW5_IMAGE_FROZEN=false`.
6. Оставить `C1/C2/C3/R`, научное выполнение, доступ к тестовому набору данных
   и публикацию закрытыми до отдельных разрешений после квитанции образа
   `QW-5`.
7. Не изменять терминальные доказательные материалы попыток 003/004/005,
   алгоритмы, часы измерения, допуски, парный порядок или реализацию среды
   выполнения.

## Проверяемая граница

```text
ATTEMPT_005_TERMINAL=true
ATTEMPT_005_VALIDATION_PASSED=true
ATTEMPT_005_RETRY_PERMITTED=false
ATTEMPT_005_AUTHORIZED_CELL_COUNT=168
ATTEMPT_005_RESERVE_PROBE_COUNT=28
ATTEMPT_005_AGGREGATE_COUNT=14
ATTEMPT_005_CPU_ORDER_EFFECT_PASS_COUNT=7
ATTEMPT_005_ROCM_ORDER_EFFECT_PASS_COUNT=7
ATTEMPT_005_ORDER_EFFECT_FAILURE_COUNT=0
QW_LC4_E_COMPLETE=true
QW5_TRANSITION_PERMITTED=true
QW5_OPEN=true
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=true
QW5_IMAGE_FROZEN=false
SCIENTIFIC_EXECUTION_OPEN=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
RUNTIME_RERUN_PERFORMED=false
NEXT_SLICE=QW-5-scientific-image-freeze
```

## Последствия

Следующая допустимая граница эффекта — только фиксация научного образа `QW-5`.
Она должна зафиксировать единственный научный образ для `C1/C2/C3/R`. До
материализации квитанции образа `QW-5` научная кампания остаётся закрытой.

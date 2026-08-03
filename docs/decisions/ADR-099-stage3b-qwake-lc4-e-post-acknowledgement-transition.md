# ADR-099: переход после материализации финального подтверждения `QW-LC4-E`

[English version](ADR-099-stage3b-qwake-lc4-e-post-acknowledgement-transition_EN.md)

- **Статус:** принят как переходный контракт; инженерный [запуск](../glossary.md#term-run) не выполнен
- **Дата:** 2026-08-02
- **Контекст:** `QW-LC4-E`
- **Предшествует:** ADR-098
- **Базовый коммит:** `c9588661e28f2eba81a9da082935968e9224a257`

## Контекст

ADR-098 выпустил отдельное одноразовое разрешение для производственной точки
вызова, материализующей финальное операторское подтверждение. После слияния
эта точка вызова была выполнена один раз. Разрешение потреблено, подтверждение
материализовано и проверено, а повтор той же попытки запрещён.

Выполненная точка вызова относится только к материализации подтверждения. Она
не является одноразовым инженерным запуском расширения `QW-LC4-E`: постоянный
файл владения v2, устойчивая квитанция исхода хоста и выход выполнения отсутствуют.

Экспериментальный план допускает переход к `QW-5` только после успешного
инженерного отчёта `QW-LC4-E`. Поэтому материализованное подтверждение является
обязательным входом будущего запуска, но не заменяет запуск и его отчёт.

## Проверенное состояние

Запечатанные [доказательные материалы](../glossary.md#term-evidence) подтверждают:

```text
ACKNOWLEDGEMENT_CALLSITE_ATTEMPT_STARTED=true
ACKNOWLEDGEMENT_CALLSITE_AUTHORIZATION_CONSUMED=true
ACKNOWLEDGEMENT_CALLSITE_SINGLE_ATTEMPT_COMPLETED=true
FINAL_EXECUTION_ACKNOWLEDGEMENT_ISSUED=true
FINAL_EXECUTION_ACKNOWLEDGED=true
ACKNOWLEDGEMENT_CALLSITE_RETRY_PERMITTED=false
ACKNOWLEDGEMENT_CALLSITE_REINVOCATION_FORBIDDEN=true
```

Тот же пакет подтверждает отсутствие эффектов инженерного запуска:

```text
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
EXTENSION_ENGINEERING_REPORT_PRESENT=false
```

Поле `callsite_invocation_pending=true` в квитанции потребления описывает
момент начала попытки. Терминальная `verification.json` отдельно подтверждает
`single_attempt_completed_state_evidence_verified=true` и материализованное
подтверждение.

## Решение

1. Считать линию точки вызова материализации завершённой, потреблённой и
   невозобновляемой.
2. Не классифицировать этот пакет как инженерный отчёт расширения.
3. Оставить `QW-5`, `C1`, `C2`, `C3`, `R`, тестовую выборку и публикацию закрытыми.
4. Запретить повторный вызов уже выполненной производственной точки вызова,
   повторное потребление её разрешения и автоматический либо ручной повтор на
   основании той же записи.
5. Разрешить только отдельный будущий срез подготовки допуска фактического
   одноразового инженерного запуска через связанный с файлом владения
   исполнитель хоста.
6. Обязать будущий срез связать материализованное подтверждение, постоянную
   цепочку доказательных материалов v2, точный образ, Torch2PC, каталог
   результата и новое отдельное одноразовое разрешение.
7. Не создавать в этом переходном срезе файл владения, исход хоста, выход
   выполнения, команду Docker или научные результаты.
8. Не изменять существующие замороженные пакеты и доказательные материалы.

## Следующий допустимый срез

```text
next_slice=QW-LC4-E-final-engineering-invocation-admission-authoring
```

Этот будущий срез подготовки допуска не выполняет модель. Он только фиксирует
машиночитаемый допуск к одной будущей атомарной операции, указывающей на
`invoke_lease_bound_host_runtime` и требующей уже материализованное финальное
подтверждение.

## Машинная граница

```text
QW_LC4_E_ACKNOWLEDGEMENT_LINE_COMPLETE=true
QW_LC4_E_ACKNOWLEDGEMENT_AUTHORIZATION_CONSUMED=true
QW_LC4_E_ACKNOWLEDGEMENT_RETRY_PERMITTED=false
QW_LC4_E_ACKNOWLEDGEMENT_REINVOCATION_FORBIDDEN=true
QW_LC4_E_EXTENSION_ENGINEERING_REPORT_PRESENT=false
QW_LC4_E_COMPLETE=false
QW5_TRANSITION_PERMITTED=false
QW5_SCIENTIFIC_IMAGE_FREEZE_OPEN=false
C1_COLLECTION_OPEN=false
C2_CALIBRATION_OPEN=false
C3_CONFIRMATORY_OPEN=false
REPLICATION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Последствия

Переходная ветка не является веткой `QW-5`. Она фиксирует различие между
завершённой материализацией подтверждения и ещё отсутствующим инженерным
отчётом расширения. Следующий запуск требует собственного допуска,
авторизации, терминальных доказательных материалов и печати репозитория.

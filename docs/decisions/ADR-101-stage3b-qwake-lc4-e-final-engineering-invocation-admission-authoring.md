# ADR-101: подготовка допуска финального инженерного вызова `QW-LC4-E`

[English version](ADR-101-stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring_EN.md)

- **Статус:** принят как подготовка допуска; [выполнение](../glossary.md#term-execution) закрыто
- **Дата:** 2026-08-03
- **Контекст:** `QW-LC4-E`
- **Предшествует:** ADR-100
- **Базовый коммит:** `5ee7d33b2d6a9092b2db473040b92ad8cda7e08f`

## Контекст

ADR-100 зафиксировал область подготовки допуска после слияния PR №168. Он
связал точные исходные пакеты, неизменяемый образ, постоянную доказательную
цепочку v2 и единственную перспективную точку
`invoke_lease_bound_host_runtime`. Фиксация области не создала запись допуска,
авторизацию, файл владения или выход [выполнения](../glossary.md#term-execution).

Текущий срез должен материализовать проверяемую запись допуска, не превращая её
в разрешение [запуска](../glossary.md#term-run). Отдельный последующий срез
обязан запечатать точный коммит репозитория и независимо проверить его до
выпуска новой одноразовой авторизации.

## Решение

Добавить чистую схему
`stage3b_qwake_lc4_final_engineering_invocation_admission.py`, отдельную
программу проверки, модульные тесты и каноническую запись `admission.json`.

Схема:

1. проверяет точные SHA-256 пяти исходных замороженных пакетов и критических
   файлов;
2. проверяет завершённую линию подтверждения и запрет её повторного вызова;
3. связывает неизменяемый образ, выходной корень, файл владения v2, устойчивый
   исход хоста и единственную перспективную точку;
4. требует новую отдельную авторизацию не более чем для одной
   [попытки](../glossary.md#term-attempt);
5. сохраняет авторизацию, разрешение вызова и все рабочие эффекты закрытыми;
6. отклоняет существующий выходной корень, файл владения v1 или v2 и устойчивый
   исход хоста;
7. не импортирует и не вызывает рабочую точку.

## Запись допуска

```text
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-v1/admission.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-v1/source-SHA256SUMS
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-authoring-v1/SHA256SUMS
```

Запись имеет собственный семантический SHA-256, связывает базовый коммит
`5ee7d33b2d6a9092b2db473040b92ad8cda7e08f` и сохраняет:

```text
FINAL_ENGINEERING_INVOCATION_ADMISSION_AUTHORED=true
FINAL_ENGINEERING_INVOCATION_ADMISSION_RECORD_PRESENT=true
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_ISSUED=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_CONSUMED=false
FINAL_ENGINEERING_INVOCATION_PERMITTED=false
FINAL_ENGINEERING_INVOCATION_STARTED=false
FINAL_ENGINEERING_INVOCATION_PERFORMED=false
EXECUTION_LEASE_V1_PRESENT=false
EXECUTION_LEASE_V2_PRESENT=false
DURABLE_HOST_OUTCOME_PRESENT=false
RUNTIME_OUTPUT_PRESENT=false
QW5_TRANSITION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Граница авторизации

Текущий срез не резервирует операторскую фразу и не создаёт идентификатор
авторизации. Будущая авторизация должна быть новой, отдельной от исторических
разрешений и действовать только после слияния и независимой проверки
репозиторной печати этого допуска. Её потребление должно быть атомарно связано с
началом единственной попытки и исключительным созданием постоянного файла
владения v2.

## Неисполняющая граница

Программа проверки не импортирует модуль рабочей точки и не вызывает
`invoke_lease_bound_host_runtime`. Отрицательные тесты изменяют только временные
копии. Текущий срез не выполняет проверку образа, не материализует команду, не
запускает Docker, модель или дочерний процесс и не создаёт рабочие артефакты.

## Последовательность

```text
admission-authoring
→ admission repository seal and independent verification
→ distinct one-shot authorization
→ atomic authorization consumption and persistent lease v2
→ invoke_lease_bound_host_runtime
→ durable host outcome
→ sealed extension engineering report
→ QW-5 eligibility decision
```

## Последствия

Запись допуска существует и проверяется, но не является авторизацией. Следующий
допустимый срез должен запечатать её точный репозиторный коммит. `QW-5`, научная
кампания, тестовая выборка и публикация остаются закрытыми.

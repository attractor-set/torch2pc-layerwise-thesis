# ADR-102: репозиторная печать допуска финального инженерного вызова `QW-LC4-E`

[English version](ADR-102-stage3b-qwake-lc4-e-final-engineering-invocation-admission-repository-seal_EN.md)

- **Статус:** принят как подготовка репозиторной печати; [выполнение](../glossary.md#term-execution) закрыто
- **Дата:** 2026-08-03
- **Контекст:** `QW-LC4-E`
- **Предшествует:** ADR-101
- **Проверенный `main`:** `d2539eb440e758c1f29b935f8599561bec7126bc`

## Контекст

ADR-101 материализовал чистую схему и каноническую запись допуска финального
инженерного вызова. PR №169 был слит с созданием отдельного коммита слияния: его точная голова
`b81c11971f1e9b78e59dd39c4d182722a3001044`, а `main` после слияния — `d2539eb440e758c1f29b935f8599561bec7126bc`. Независимая проверка после слияния
подтвердила двухкоммитный граф, точную область из 17 файлов, успешные проверки
финальной головы, `ruff`, четыре статические проверки и 23 направленных теста.

Запись допуска ещё не может быть основанием для авторизации. Сначала отдельная
репозиторная печать должна связать её с конкретным проверенным состоянием
`main`, быть слита и снова независимо проверена.

## Решение

1. Материализовать двухфайловый пакет
   `stage3b-qwake-lc4-e-final-engineering-invocation-admission-repository-seal-v1`.
2. Связать квитанцию с PR №169, точным коммитом слияния, обоими родителями,
   временем слияния, двумя PR-коммитами и областью из 17 файлов.
3. Зафиксировать семантическую контрольную сумму допуска и SHA-256 записи
   допуска, реестров, модуля, программы проверки и исправленного теста.
4. Зафиксировать только проверенное инженерное состояние репозитория, а не
   артефакт выполнения или научный результат.
5. Сохранить новую авторизацию, фразу оператора, команду вызова, файл владения
   v2, устойчивый исход хоста и выход среды выполнения отсутствующими.
6. До слияния и независимой проверки этой печати после слияния запретить
   даже отдельную подготовку новой одноразовой авторизации.

## Репозиторная квитанция

```text
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-repository-seal-v1/receipt.json
experiments/frozen/stage3b-qwake-lc4-e-final-engineering-invocation-admission-repository-seal-v1/SHA256SUMS
```

Она связывает:

```text
FINAL_ENGINEERING_INVOCATION_ADMISSION_PR=169
FINAL_ENGINEERING_INVOCATION_ADMISSION_PR_HEAD=b81c11971f1e9b78e59dd39c4d182722a3001044
FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_MAIN_COMMIT=d2539eb440e758c1f29b935f8599561bec7126bc
FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_SEAL_MATERIALIZED=true
FINAL_ENGINEERING_INVOCATION_ADMISSION_REPOSITORY_SEAL_COMPLETE=false
FINAL_ENGINEERING_INVOCATION_AUTHORIZATION_AUTHORING_PERMITTED=false
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
PUBLICATION_PERMITTED=false
```

## Неисполняющая граница

Этот срез не импортирует и не вызывает `invoke_lease_bound_host_runtime`, не
инспектирует образ, не обращается к Docker, не создаёт дочерний процесс и не
изменяет границу среды выполнения. Он только материализует проверяемую репозиторную
квитанцию и документацию.

## Последовательность

```text
admission authoring merged and verified
→ admission repository seal authoring
→ repository-seal merge and independent verification
→ distinct one-shot authorization authoring
→ authorization merge and independent verification
→ atomic authorization consumption, attempt start, and lease v2
→ invoke_lease_bound_host_runtime
→ durable host outcome
→ sealed extension engineering report
→ QW-5 eligibility decision
```

## Последствия

Репозиторная печать материализована, но не завершена до собственного слияния и
независимой проверки. Авторизация не создана и её подготовка пока не разрешена.
`QW-5`, научная кампания, тестовая выборка и публикация остаются закрытыми.

# ADR-064: авторинг закрытого при ошибке допуска `QW-LC4-E`

[English version](ADR-064-stage3b-qwake-lc4-e-execution-admission-authoring_EN.md)

- **Статус:** принят как авторинг допуска `QW-LC4-E`;
  [выполнение](../glossary.md#term-execution) не начато
- **Дата:** 27 июля 2026 года

## Контекст

`QW-LC4-F` завершён после слияния PR №124 и независимой проверки коммита слияния
`453bb4eb6a20ae52a0d10384a1c54e45cf999143`. Зафиксированное разрешение
допускает одну инженерную [попытку](../glossary.md#term-attempt), но само по
себе не должно запускать [локальное вычисление](../glossary.md#term-local-compute).

Необходимо разделить три состояния:

1. разрешение существует в неизменяемом пакете;
2. контур управления проверил условия потребления разрешения;
3. модельное выполнение действительно началось.

Без отдельного допуска проверка разрешения может быть ошибочно принята за
начало выполнения или за наличие [доказательных материалов](../glossary.md#term-evidence).

## Решение

Добавить чистую схему `stage3b_qwake_lc4_execution_admission.py` и программу
проверки будущего допуска. Они:

- повторно проверяют точный десятифайловый пакет `QW-LC4-F`;
- различают коммит слияния контура управления и исходный коммит неизменяемого
  образа;
- требуют точное подтверждение оператора;
- требуют отсутствия каталога результатов и файла одноразового владения;
- допускают ровно одну инженерную попытку;
- сохраняют `runtime_execution_started=false`;
- сохраняют научное выполнение, доступ к
  [набору данных](../glossary.md#term-dataset) и публикацию закрытыми.

Схема не импортирует модельный исполнитель, не создаёт каталог результатов,
не создаёт файл владения и не записывает запись допуска.

## Идентичности

```text
qwake_lc4_f_merge_commit=453bb4eb6a20ae52a0d10384a1c54e45cf999143
frozen_runtime_source_commit=51fc7537fdcb395145fc4c5a38b8918b018fe892
torch2pc_commit=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
image_digest=sha256:a31cf96e20ab45ce29fe18b68eb805bd048a02f1f8107cf680d1c174ea363929
preflight_sha256=sha256:3a8d7817338f3b93396270ea8e1b1b2fbda768dbd5461a18f97520948a53a9e6
authorization_sha256=sha256:d11b662a5c5eeada5333e69c6fddf2e50726c01b4d8c78a556a68167dbdd301e
authorized_output_root=results/stage-3/qwake-lc4-runtime-validation-v1-attempt-001
```

## Границы

```text
QW_LC4_F_COMPLETE=true
QW_LC4_E_BRANCH_OPEN=true
EXECUTION_ADMISSION_IMPLEMENTED=true
EXECUTION_ADMISSION_ISSUED=false
QW_LC4_E_EXECUTION_PERMITTED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
```

## Последствия

Следующий отдельный срез должен зафиксировать конкретную запись допуска,
связанную с точным коммитом контура управления. Только после его независимой
проверки можно реализовать одноразовый файл владения и исполняющую обёртку.

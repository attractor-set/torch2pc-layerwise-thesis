# ADR-066: проектирование файла владения и исполняющей обёртки `QW-LC4-E`

[English version](ADR-066-stage3b-qwake-lc4-e-execution-lease-wrapper-authoring_EN.md)

- **Статус:** принят как срез проектирования; [выполнение](../glossary.md#term-execution) не начато
- **Дата:** 27 июля 2026 года

## Контекст

Фиксация допуска `QW-LC4-E` слита в `main` коммитом
`12b7d24153a681f731a43e8497275016ad4e1656` и независимо проверена. Запись допуска разрешает одну
инженерную [попытку](../glossary.md#term-attempt), но файл исключительного
владения ещё не создан, разрешение не потреблено и модельное выполнение не
начато.

Перед добавлением эффектов требуется явно определить:

1. каноническую предварительную схему одноразового файла владения;
2. точную привязку владения к слитой записи допуска, образу, Torch2PC и
   будущему коммиту обёртки;
3. контракт будущей исполняющей обёртки;
4. правила исключительного захвата владения, отсутствия повторной попытки
   после захвата и атомарного продвижения результатов.

## Решение

Добавить чистый модуль `stage3b_qwake_lc4_execution_wrapper.py` и программу
проверки без записи. Они:

- повторно проверяют точный пятифайловый пакет допуска и его два реестра
  SHA-256;
- проверяют полную матрицу из 168 ячеек, порядок CPU/ROCm и 28 резервных
  проверок;
- строят только в памяти предварительную запись владения, которая при будущем
  захвате должна потребить разрешение;
- строят только в памяти контракт исполняющей обёртки;
- требуют атомарный исключительный захват, сохранение записи владения после
  ошибки, запрет повтора после захвата и атомарное продвижение каталога
  результатов;
- сохраняют научное выполнение, доступ к
  [набору данных](../glossary.md#term-dataset) и публикацию закрытыми.

Этот срез не содержит программы записи владения, исполнителя рабочей среды,
программы записи результатов, вычислительного модуля или материализованного
файла владения. Значение `authorization_consumed=true` относится только к
тестовому образцу будущего захвата; текущее состояние репозитория остаётся
`AUTHORIZATION_CONSUMED=false`.

## Точные идентичности

```text
admission_freeze_merge_commit=12b7d24153a681f731a43e8497275016ad4e1656
admission_freeze_head_commit=52e8bbd54bdea70abbd9e7aff86872b69a8c341d
torch2pc_commit=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
admission_sha256=sha256:d1ee6d022588f0a2cf0ac23f3bf8de9b27f9aad4fc1153435bd70e1ab83e296c
admission_package_registry_sha256=sha256:411f3e8d62b367755a6f02070ad84bc6f37cfefad602d885674a844b57aa74cd
admission_source_registry_sha256=sha256:01c9a29d1f80098707d6715ffd5160ad48bb497b08a71180c2b71d8e89b66504
module_sha256=sha256:34980a70d76b582d70333034b4a259b50bd948bb751888f17db9a988c2c77a9b
validator_sha256=sha256:5ce921dc10f95320191effce0b57caef0bbd528550587c4ad443c71b516b75c6
test_sha256=sha256:b7b28b17ab80679ea3653fd1b3586053172c6b74967fa9247a58b404f8042e60
prospective_test_vector_lease_sha256=sha256:66961a641d7f9cc9b7b2f958c432a492c1ada171056b827136171dd0df2b355a
prospective_test_vector_wrapper_contract_sha256=sha256:0ff0cf0b0f23bf21d65567079212e5bad04e16e257815143d3f581664fa4dbf0
authorized_cell_count=168
reserve_probe_count=28
```

## Границы

```text
ADMISSION_FREEZE_MERGED=true
EXECUTION_LEASE_WRAPPER_AUTHORING_BRANCH_OPEN=true
EXECUTION_LEASE_SCHEMA_IMPLEMENTED=true
EXECUTION_WRAPPER_CONTRACT_IMPLEMENTED=true
EXECUTION_LEASE_MATERIALIZED=false
EXECUTION_LEASE_WRITER_PRESENT=false
RUNTIME_EXECUTOR_PRESENT=false
RESULT_WRITER_PRESENT=false
QW_LC4_E_EXECUTION_PERMITTED=false
AUTHORIZATION_CONSUMED=false
RUNTIME_EXECUTION_STARTED=false
RUNTIME_EXECUTION_PERFORMED=false
ENGINEERING_EVIDENCE_PRESENT=false
SCIENTIFIC_EXECUTION_OPEN=false
TEST_DATASET_ACCESS=false
PUBLICATION_PERMITTED=false
LOCAL_COMPUTE_EXECUTION_OPEN=false
```

## Последствия

Следующий отдельный срез после слияния и независимой проверки может
реализовать атомарную программу записи владения и конкретную исполняющую
обёртку. Их наличие также не должно автоматически создавать файл владения или
запускать [запуск](../glossary.md#term-run). Фактический захват и запуск
требуют отдельной неизменяемой фиксации выполнения.

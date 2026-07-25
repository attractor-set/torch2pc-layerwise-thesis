# ADR-047: фиксация нового допуска `QW-4B-F-v2` для одноразовой проверки среды

[English version](ADR-047-stage3b-qwake-fp-runtime-validation-freeze-v2_EN.md)

- **Статус:** принято как `QW-4B-F-v2`; одна инженерная [попытка](../glossary.md#term-attempt) разрешена, но [выполнение](../glossary.md#term-execution) и [доказательные материалы](../glossary.md#term-evidence) отсутствуют
- **Дата:** 2026-07-24

```text
qwake_new_image_built=true
qwake_new_runtime_preflight_captured=true
qwake_new_runtime_authorization_issued=true
qwake_runtime_authorization_verified=true
qwake_runtime_validation_permitted=true
qwake_authorized_cell_count=6
qwake_authorized_execution_count=1
qwake_runtime_execution_performed=false
qwake_engineering_evidence_present=false
qwake_scientific_execution_open=false
qwake_next_slice=QW-4B-E-v2
```

## Контекст

`ADR-046` вывел старый [кандидат](../glossary.md#term-candidate) `QW-4B-F-v1` из обращения до [запуска](../glossary.md#term-run) и потребовал новый неизменяемый образ после полного рефакторинга документации. Новый образ собран из коммита слияния `e413bb1e13cee42f702512e499f994e90df21e45` и связан с точным состоянием Torch2PC `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4`.

До выпуска разрешения в том же образе повторно прошли статические, модульные и документальные проверки, а живая предварительная проверка [среды выполнения](../glossary.md#term-runtime) связала CPU/float64 и ROCm/float32. Ни одна модельная ячейка при этом не выполнялась.

## Решение

### 1. Неизменяемые идентичности

```text
source_commit=e413bb1e13cee42f702512e499f994e90df21e45
torch2pc_commit=b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4
image_digest=sha256:bd91fab26df5f91a3aba90b8cad38badccab3a1a7bfb20efe4126a88a13236c4
preflight_sha256=sha256:79ead4a0e757272c788acd90700d61c0e5a0509fe64168f83f47dc0963ce4d00
authorization_sha256=sha256:d22063efa0c458c2498577139fa322b952081d8356cd1a6511f25188b12206b6
receipt_chain_sha256=sha256:9eda60c6806581fea28021546b881d939e062c017b702a175105c56a25dea05d
authorized_output_root=results/stage-3/qwake-fp-runtime-validation-v2-attempt-001
```

Образ, исходный код, предварительная проверка, квитанция статических проверок, разрешение и журнал его проверки образуют одну адресуемую по содержимому цепочку.

### 2. Побайтовое сохранение внешних входов

Восемь внешних файлов перенесены без изменения. `source-SHA256SUMS` сохраняет исходный реестр, а новый `SHA256SUMS` покрывает весь зафиксированный пакет, включая манифест. Это является [фиксацией целостности](../glossary.md#term-integrity-sealing), а не результатом вычисления модели.

```text
source_registry_sha256=sha256:40ce845bc50dbbbdcc7aef5b4327e1325dd7bcda9c5c85a61ebb05024e045caa
package_registry_sha256=sha256:d6d9d6b4b4fb2614e928b16c8acd355508aebee7561254505828f9479ee31a30
source_files_preserved_byte_for_byte=true
```

### 3. Ограниченная область разрешения

```text
CPU/float64 × P0/P1/P2
ROCm/float32 × P0/P1/P2
model_seed=0
batch_id=synthetic-engineering-batch-v1
execution_count=1
```

Разрешение открывает только инженерную проверку среды выполнения. Научная кампания, тестовая выборка, публикация, заморозка научного образа и `LOCAL_COMPUTE` остаются закрытыми.

### 4. Проверка разрешения не является выполнением

Официальная программа проверки повторно проверила исходный код, Torch2PC, образ, предварительную проверку, цепочку квитанций, идентичности CPU/ROCm и отсутствие каталога результатов. Проверка не вызывала исполняющую команду и не использовала одноразовую попытку.

```text
authorization_verified=true
runtime_execution_performed=false
engineering_evidence_present=false
```

### 5. Следующий атомарный срез

Только после слияния `QW-4B-F-v2` допускается отдельный `QW-4B-E-v2`. Исполняющий срез обязан использовать точный зафиксированный пакет и создать каталог результатов ровно один раз. Любое несовпадение идентичности или уже существующий каталог закрывает [запуск](../glossary.md#term-run) с ошибкой.

`QW-LC0` остаётся закрытым до успешного запечатанного базового инженерного отчёта.

## Последствия

`QW-4B-F-v2` подтверждает готовность допуска, но не невмешательство наблюдателей и не корректность стоимости на реальном выполнении. Эти утверждения могут появиться только после `QW-4B-E-v2` и отдельной проверки результатов.

# ADR-119: проект замыкания исходников для `attempt-003`

## Статус

Принято как ограниченное проектирование без вычислительного эффекта.

## Контекст

`attempt-002` завершён как необратимо неуспешная
[попытка](../glossary.md#term-attempt). Следующая идентичность —
`stage3b-qwake-lc4-runtime-validation-v1-attempt-003` — не является повтором прежней попытки.

Сбой показал, что `host-side registry` недостаточен для доказательства наличия
всех файлов внутри будущего образа. Новый контракт обязан отделить
проектирование от [выполнения](../glossary.md#term-execution) и ввести
замыкание исходников до любой сборки, выдачи `authorization` или внешнего
эффекта.

## Решение

1. Зафиксировать машиночитаемый `contract.json` с новым `attempt_id`,
   `results/stage-3/qwake-lc4-runtime-validation-v1-attempt-003` и новыми идентичностями будущих пакетов.
2. Будущий `runtime package` обязан содержать `runtime-SHA256SUMS` со всеми
   `build/runtime inputs`, перечисленными в контракте.
3. До `docker build` каждый путь проверяется как `Git object`, его `blob bytes`
   сверяются по `SHA-256`, а `inclusion` проверяется относительно
   `.dockerignore`. Результат сохраняется как детерминированный `closure report`.
4. После `COPY . /workspace` `Dockerfile` обязан выполнить `sha256sum -c`
   для `runtime-SHA256SUMS` до фиксации финальной `image identity`.
5. После сборки `OCI revision` должна совпадать с точным `source commit`; `image`
   `digest` должен быть новым; `build-time proof` и неисполняющая `container-side`
   проверка обязательны.
6. Повторное использование `attempt-002` `authorization`, `image identity`,
   `lease` или `outcome` запрещено.
7. На текущем срезе запрещены [запуск](../glossary.md#term-run), доступ к
   [набору данных](../glossary.md#term-dataset), вызов `model code`, создание
   `lease/outcome`, сборка или запуск `Docker`, `materialization freeze/host chain`,
   `merge` `PR #179`, изменение `remote` `main` и открытие `QW-5`.

## Граница

Этот ADR описывает только `design authoring`. Он не реализует `runtime`,
не материализует `runtime-SHA256SUMS`, не создаёт `image`, `freeze`, `host chain`,
`authorization`, `operation`, `lease`, `output root` или `durable outcome`.

Отдельное разрешение требуется для каждого следующего шага:
`implementation authoring`, `image build`, `freeze materialization`, `host chain`,
`authorization issuance`, `operation authoring` и фактического выполнения.

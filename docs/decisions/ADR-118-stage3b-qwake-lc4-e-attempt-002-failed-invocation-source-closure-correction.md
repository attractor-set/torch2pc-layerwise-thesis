# ADR-118: терминализация attempt-002 и исправление временного source closure

- **Статус:** принято как неисполняющее corrective authoring-решение
- **Дата:** 2026-08-05
- **Связанные решения:** ADR-113, ADR-114, ADR-115, ADR-117

## Контекст

Одноразовый вызов ADR-117 достиг operation entrypoint, delegated transition
и `docker run`, но контейнер завершился до создания lease-v1. Durable host
outcome записан; lease и output root отсутствуют; authorization не
потреблена по lease-семантике.

Образ был построен из commit
`02afcc3e79b2d456cc3f1c075d4d792a0be608f7`. Относительно окончательного
execution-freeze `source-SHA256SUMS` этот commit содержит десять byte-exact
путей и не содержит два пути:

- `scripts/verify_stage3b_qwake_lc4_attempt_002_execution_freeze.py`;
- `tests/unit/test_stage3b_qwake_lc4_attempt_002_execution_freeze.py`.

Commit материализации execution freeze
`2f346498a28377d355b88560aa099890f829af46` уже содержит оба пути, но их
содержимое ещё не совпадает с окончательным registry: десять путей exact,
два имеют hash mismatch.

Первым commit, в котором все двенадцать registry entries одновременно
существуют и byte-exact совпадают, является authorization commit
`b5b29be5802641287e6e29bb42240ad9e41744b4`.

Следовательно, источник образа, execution-freeze materialization и
окончательная registry identity относятся к трём разным временным срезам.
Host preflight проверял текущий control-plane tree, а runtime проверял
более старый `/workspace` образа.

## Решение

1. Attempt-002 объявляется терминальной неуспешной необратимой попыткой.
2. Durable outcome, freeze-v1, authorization-v1, host-chain, operation и
   обе invocation scripts сохраняются без изменений.
3. Повтор attempt-002 и повторное использование его authorization decision
   запрещены.
4. Следующая вычислительная попытка получает identity attempt-003 и
   полностью непересекающиеся пути эффектов.
5. Runtime source registry отделяется от host authoring source registry.
6. До сборки каждый runtime registry path проверяется по blob exact source
   commit.
7. После `COPY . /workspace` Docker build обязан проверить runtime registry.
8. После сборки независимый gate проверяет image digest, OCI revision и
   container-side source closure без model/dataset execution.
9. Future authorization выдаётся только после полного image/source-closure
   proof.

## Граница

Этот срез не строит образ, не запускает контейнер, не создаёт attempt-003,
не выдаёт authorization, не создаёт lease/output, не разрешает merge PR
#179 и не открывает QW-5.

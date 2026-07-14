# ADR-010: изоляция Stage 3B B0 canonical cells по процессам

- Статус: принято
- Дата: 2026-07-14
- Область: Stage 3B B0 canonical execution lifecycle
- Базовый commit: `f40db15e65cb3f701711ce5b41732e9b87d6104a`

## Контекст

ROCm/float32 canonical protocol содержит 96 cells. Предыдущий runner выполнял их последовательно в одном Python-процессе. Отдельные тяжёлые FixedPred и Strict cells в свежих процессах использовали около 310–312 MiB reserved VRAM, но общий процесс после 16 завершённых cells удерживал около 11.5 GiB allocations. Первый HIP `OutOfMemoryError` не остановил lane, поэтому были созданы ещё 80 failed attempts.

Проблема относится к lifecycle и владению GPU runtime state между cells. Она не меняет Stage 3B protocol contract, scientific measurements или Stage 3A evidence.

## Решение

Production canonical lane использует следующую последовательность для каждой выбранной cell:

1. Parent controller сохраняет immutable snapshots authorization и manifest внутри уникального run directory.
2. Parent запускает новый Python interpreter через `python -m torch2pc_thesis.stage3b_canonical_child`.
3. Child повторно проверяет authorization и canonical lane, выполняет ровно одну cell через существующий `execute_canonical_cell()` и завершает процесс.
4. Parent определяет единственный новый attempt directory и принимает ровно один terminal record: `completed.json` или `failed.json`.
5. Parent сверяет identity, authorization token, manifest digest, source commit, lane, image digest, canonical protocol, attempt id и attempt directory.
6. Parent фиксирует terminal SHA-256 и process telemetry: parent PID, child PID, exit code, timestamps, stdout/stderr digests и ограниченные tails.
7. Только после успешной terminal validation parent переходит к следующей cell.

Каждая production cell получает отдельный Python/HIP context. Завершение child process является границей освобождения process-owned GPU allocations; `torch.cuda.empty_cache()` не используется как замена process isolation.

## Fail-fast policy

Валидированный failed terminal классифицируется как systemic resource failure, когда наблюдается одно из условий:

- `OutOfMemoryError`;
- сообщение `HIP out of memory`;
- сообщение `CUDA out of memory`;
- эквивалентный HIP/CUDA allocation error.

После первого такого события parent завершает цикл cells. Текущая failed cell сохраняет один attempt; все последующие cells остаются pending, и attempts для них не создаются. Lane получает `lane_incomplete`, `stopped_early=true` и `systemic_stop` с provenance исходной ошибки.

Обычная независимая ошибка одной cell сохраняет прежнюю policy: failed terminal записывается, а parent может продолжить остальные cells.

## Interruption и resume

Если child или parent прерывается после `started.json`, но до terminal record, attempt остаётся running. Следующий запуск без `--resume` отклоняется существующим planner. Явный `--resume` переводит такой attempt в retryable в пределах `max_attempts`.

Invalid или отсутствующий terminal record считается lifecycle violation. Parent записывает доступную process telemetry, aborts lane и не запускает следующую cell.

## Canonical boundaries

- Production canonical execution остаётся только `rocm/float32`.
- Internal child также отклоняет CPU/float64.
- CPU/float64 сохраняется только для bounded smoke и injected engineering-control tests.
- Canonical protocol остаётся 96 cells, 20 warm-up, 50 measured, 5 repetitions.
- `evidence=false`, publication disabled и test dataset inaccessible сохраняются.
- Stage 3A artifacts и checksums не изменяются.

## Consequences

Положительные последствия:

- bounded VRAM lifetime на уровне одной cell;
- отсутствие cross-cell allocator retention;
- fail-fast вместо каскада OOM attempts;
- проверяемая связь process → attempt → terminal record;
- сохранение существующих lock, plan, retry и resume semantics.

Стоимость:

- один interpreter startup на cell;
- дополнительные run-local snapshots и process telemetry records;
- production runner требует доступности текущего package через тот же Python executable.

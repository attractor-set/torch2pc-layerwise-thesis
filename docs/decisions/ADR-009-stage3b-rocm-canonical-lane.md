# ADR-009: ROCm/float32 как единственная canonical lane Stage 3B B0

[English version](ADR-009-stage3b-rocm-canonical-lane_EN.md)

- Статус: принято как corrective protocol decision;
- дата: 2026-07-14;
- область: Stage 3B B0 profiling;
- затрагивает Stage 1/2 и опубликованный Stage 3A evidence: нет.

## Контекст

Preregistered Stage 3 profiling matrix содержит 336 cells, из которых 96 принадлежат B0 `stage2_baseline`. Device не является дополнительной осью этой матрицы. Дублирование каждой B0 cell на CPU и ROCm создало бы 192 B0 executions и 672 Stage 3 executions, что не соответствует зафиксированному design.

CPU/float64 ранее использовался как инженерный correctness/control environment для smoke, non-perturbation и targeted equivalence gates. Он был ошибочно включён в campaign authorization как вторая обязательная canonical performance lane.

Ошибочная CPU lane была остановлена memory-cgroup OOM killer после 21 завершённой cell и одной незавершённой попытки. При завершении Python-процесс имел приблизительно 50 202 008 KiB anonymous RSS. Все CPU attempts сохранились immutable, имеют `evidence=false`, `full_lane_complete=false` и исключаются из confirmatory results.

## Решение

1. Единственная canonical B0 performance lane — `rocm/float32`.
2. Canonical design содержит ровно 96 executions: 48 FixedPred и 48 Strict.
3. Canonical protocol остаётся `20 warm-up × 50 measured × 5 repetitions`.
4. `cpu/float64` остаётся engineering control lane только для bounded smoke и targeted equivalence checks.
5. CPU control не участвует в `full_lane_complete`, `full_campaign_complete` или confirmatory performance evidence.
6. Authorization требует ровно один canonical preflight — ROCm/float32. CPU preflight может быть приложен только как optional engineering-control record.
7. Canonical CLI отклоняет CPU до создания lock, lane directory или attempt.
8. Machine-readable source of truth: `experiments/planned/STAGE3B-B0-PROTOCOL-CONTRACT.json`.
9. Authorization schema повышается до version 2, domain и scope меняются; version 1 и старый двух-lane token считаются retired и не могут быть resumed.

## Последствия

После merge требуется новый project freeze, новый image digest, новый output root, новый ROCm preflight и новый authorization token. Старые CPU attempts и старый token сохраняются как audit trail, но не используются для научных выводов.

Stage 3A results, SHA manifests, B0 manifest ordering, seeds, methods, depth/width/batch grid и Torch2PC source commit остаются неизменными.

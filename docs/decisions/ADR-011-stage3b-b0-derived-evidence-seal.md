# ADR-011: производный evidence seal для Stage 3B B0

[English version](ADR-011-stage3b-b0-derived-evidence-seal_EN.md)

## Контекст

Stage 3B B0 canonical lane завершает 96 ROCm/float32 cells и сохраняет raw
records как non-evidence execution artifacts. Эти records намеренно содержат
`evidence=false`, `full_campaign_complete=false` и
`results_publication_permitted=false`: runner не должен одновременно исполнять
эксперимент и разрешать публикационные утверждения.

После corrective process-isolation run raw output был перенесён в отдельный
постоянный архив и закреплён `SHA256SUMS`. Ручное изменение terminal records,
`lane-state.json` или authorization chain нарушило бы provenance.

## Решение

Stage 3B B0 получает отдельную read-only validation, aggregation and sealing
pipeline.

Pipeline:

1. требует ожидаемые execution source commit, sealing implementation source
   commit, image digest и SHA-256 файла `SHA256SUMS`;
2. проверяет точное соответствие inventory всем файлам архива;
3. проверяет freeze, ROCm preflight, authorization, manifest snapshot,
   lane state, run terminal, 96 attempts и 96 process records;
4. повторно проверяет numerical integrity и полноту region measurements;
5. агрегирует compact seed-level и paired tables;
6. создаёт новый content-addressed derivative bundle вне raw archive;
7. повторно проверяет raw archive перед завершением записи.

Raw archive остаётся неизменяемым и сохраняет исходные non-evidence flags.
Только производный seal получает:

- `evidence=true`;
- `full_b0_campaign_complete=true`;
- `results_publication_permitted=true`;
- `full_stage3b_campaign_complete=false`.

Последнее поле фиксирует, что завершён только baseline candidate B0, а не вся
расширенная Stage 3B candidate campaign.

## Статистическая единица

`model_seed` остаётся статистической единицей. Repetitions, measured steps и
profiling regions агрегируются как повторные наблюдения внутри seed. Paired
FixedPred/Strict tables связываются по depth, width, batch size и model seed.

## Последствия

- Execution code не изменяет публикационный статус.
- Raw records и Stage 3A evidence не меняются.
- Derived tables можно хранить и публиковать независимо от большого raw
  archive.
- Любое изменение source archive, missing attempt, failed terminal, process
  isolation violation или numerical integrity failure блокирует sealing.
- Seal фиксирует отдельные execution и sealing implementation commits.
- Повторный sealing одинакового archive тем же sealing commit создаёт тот же
  `seal_digest`.

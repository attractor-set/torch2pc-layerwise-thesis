# Дорожная карта

[English version](ROADMAP_EN.md)

## Фазы 1–5 — завершены

1. Research scaffold и preregistration.
2. Controlled environment и validation-only pilot 96/96.
3. Stage 1 confirmatory campaign 80/80.
4. Stage 2 implementation study 80/80.
5. Public release и проверка неавторизованного доступа.

## Фаза 6 — Stage 3 design revision 2 завершена

Закреплены locality/profiling contracts, exact candidates, core
approximations и predict-correct candidates.

## Фаза 7 — Stage 3A layer-wise diagnostics завершена

- same-state gradient probes: seeds 0–9;
- independently trained representation probes: seeds 0–9;
- Exact–BP controls: 10/10 passed;
- опубликованы агрегированные gradient, CKA и RSA evidence-таблицы;
- raw observations сохраняются отдельно от Git.

## Фаза 8 — Stage 3A statistical publication — текущая

- парная статистика по model seed;
- Holm-коррекция внутри заранее определённых семейств;
- effect sizes и интервалы;
- gradient/depth и representation figures;
- evidence tag и replication bundle.

## Фаза 9 — locality и exact execution

Выполнить B0/A0 profiling, затем B1/B2 gates и attribution. Эти эксперименты
не изменяют завершённый Stage 3A diagnostic evidence-набор.

## Фаза 10 — core approximations и predict-correct

C1/C2 и C4/C5 проходят отдельные validation-only screening campaigns с
residual, fallback, non-inferiority и VJP-reduction gates.

## Фаза 11 — расширенный Stage 3 freeze и final

Заморозить выбранные candidates и параметры, создать отдельные execution и
publication states и только после freeze разрешить final test evaluation.

## Фаза 12 — диссертация и статья

Объединить Stage 1/2, Stage 3A diagnostics и последующие locality/acceleration
результаты, подготовить replication bundles и clean-room reproduction.

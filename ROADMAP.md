# Дорожная карта

[English version](ROADMAP_EN.md)

## Фазы 1–5 — завершены

1. Исследовательский каркас и предварительная регистрация.
2. Контролируемая среда и пилот только на валидационной выборке 96/96.
3. Подтверждающая кампания Stage 1 — 80/80.
4. Исследование реализации Stage 2 — 80/80.
5. Публичный выпуск и проверка неавторизованного доступа.

## Фаза 6 — Stage 3 design revision 2 завершена

Закреплены locality/контракт профилированияs, exact candidates, core
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
- evidence tag и пакет воспроизведения.

## Фаза 9 — locality и exact execution

Выполнить B0/A0 profiling, затем B1/B2 gates и attribution. Эти эксперименты
не изменяют завершённый Stage 3A diagnostic evidence-набор.

## Фаза 10 — core approximations и predict-correct

C1/C2 и C4/C5 проходят отдельные validation-only screening campaigns с
residual, fallback, non-inferiority и VJP-reduction gates.

## Фаза 11 — расширенный Stage 3 — заморозка протокола и итоговый запуск

Заморозить выбранные candidates и параметры, создать отдельные execution и
publication states и только после freeze разрешить final test evaluation.

## Фаза 12 — диссертация и статья

Объединить Stage 1/2, Stage 3A diagnostics и последующие locality/acceleration
результаты, подготовить пакет воспроизведенияs и независимое воспроизведение в чистой среде.

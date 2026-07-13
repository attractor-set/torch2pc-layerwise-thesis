# Дорожная карта

[English version](ROADMAP_EN.md)

Номера фаз ниже относятся к дорожной карте репозитория. Названия
экспериментальных кампаний Stage 1, Stage 2 и возможный Stage 3 сохраняются
отдельно.

## Фаза 1. Исследовательский scaffold — завершена

- нейтральная исследовательская позиция и preregistration draft;
- test isolation и pilot-freeze gate;
- append-only registry, splits и checksums;
- Docker/ROCm scaffold и статические проверки.

## Фаза 2. Среда и validation pilot — завершена

- закреплены Ubuntu/ROCm environment и исходный Torch2PC;
- CPU/GPU C0/C1 gates пройдены;
- validation-only pilot завершён 96/96 без test;
- FixedPred и Strict configurations выбраны и заморожены.

## Фаза 3. Stage 1 confirmatory campaign — завершена

- 80/80 ячеек на исходном Torch2PC;
- 0 failed cells;
- test открыт только в final;
- результаты, manifests и publication tables сформированы;
- tag: `confirmatory-final-v1`.

## Фаза 4. Stage 2 implementation study — завершена

- implementation-preserving Torch2PC patch зафиксирован;
- original-vs-patched CPU/GPU gates пройдены;
- парная матрица 80/80 завершена;
- quality Stage 1/2 совпало попарно;
- cross-version runtime analysis сформирован;
- execution tag: `stage2-execution-v1`;
- results tag и Release: `stage2-results-v1`.

## Фаза 5. Public release — завершена

- replication bundle опубликован и проверен;
- public-facing документация синхронизирована;
- repository visibility изменена на public;
- неавторизованный доступ к README, tags, Release assets, Actions и Security
  policy проверен.

## Фаза 6. Stage 3 diagnostics — необязательная

Stage 3 создаётся только как отдельный заранее описанный эксперимент. Возможные
направления:

- новые performance changes;
- послойные градиенты;
- CKA/RSA с учётом вариации между seeds;
- устойчивость к искажениям;
- equal-wall-clock comparison;
- architecture и dataset transfer.

Stage 3 не является условием завершённости Stage 1/2 или public visibility.

## Фаза 7. Текст диссертации и статьи — продолжается

- переносить только зарегистрированные наблюдения;
- разделять результат, интерпретацию и ограничения;
- ссылаться на execution и publication states явно;
- выбирать последующий archival/DOI release с учётом требований площадки.

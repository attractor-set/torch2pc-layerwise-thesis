# Статус исследования

[English version](STATUS_EN.md)

Состояние после завершения validation pilot и двух 80-ячеечных подтверждающих
серий. Stage 1 использует исходный Torch2PC, Stage 2 — закреплённый
implementation-preserving patch. Численные контроли ограничены закреплённой
экспериментальной областью и не трактуются как универсальное доказательство для
любых моделей и сред.

| Компонент | Наблюдаемый статус |
|---|---|
| Validation-only pilot | 96/96 terminal-ячеек, 0 failed, test не вычислялся |
| Stage 1 final | 80/80 completed, 0 failed |
| Stage 2 final | 80/80 completed, 0 failed |
| Модель и данные | `lenet_classic`, MNIST и FashionMNIST |
| Исходный Torch2PC | `00c6c50ee3540537bbb56ab2b6567b541f42b093` |
| Patched Torch2PC | `b20d9142e4bdbf57b3ec8bf9f9c4472372ec8db4` |
| Stage 1 source lock | `140e77cc2083bf04234dcea16b95803e63cb0537` |
| Stage 2 execution source | `6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` |
| Stage 2 results state | `bb435432a65b76b7fc4f383b566b9a372fc346ae` |
| CPU/GPU equivalence gates | Пройдены |
| Regression suite | 63 passed |
| Stage 1 / Stage 2 quality | Парные test accuracy и macro-F1 совпали |
| Производительность Stage 2 | `BP ≈ Exact < FixedPred << Strict` |
| Cross-version analysis | `results/cross-version/` |
| Torch2PC equivalence audit | `docs/torch2pc-patched-v1-equivalence.md` |

## Публикационное состояние

- Stage 1 tag: `confirmatory-final-v1`;
- Stage 2 execution tag: `stage2-execution-v1`;
- Stage 2 results tag: `stage2-results-v1`;
- GitHub Release `stage2-results-v1` опубликован;
- replication bundle содержит raw Stage 2 artifacts;
- SHA-256 и file manifest опубликованы вместе с архивом;
- по manifest проверено 660 artifacts.

Execution commit и publication state являются разными provenance points:
`6d66b0a6...` фиксирует код исполнения Stage 2, а `bb435432...` фиксирует
последующее состояние с собранными и опубликованными результатами.

## Следующий шаг

Stage 1 и Stage 2 закрыты. Текущий операционный шаг — public visibility и
последующая проверка доступности README, tags, Release assets и CI для
неавторизованного посетителя. Stage 3 остаётся необязательным и создаётся только
как отдельная кампания для новых performance changes или расширенной
диагностики.

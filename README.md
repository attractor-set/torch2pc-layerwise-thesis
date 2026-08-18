# Torch2PC Layer-wise Thesis

[English version](README_EN.md)

![Python](https://img.shields.io/badge/Python-3.12-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.9.1-ee4c2c)
![ROCm](https://img.shields.io/badge/ROCm-7.2.1-ED1C24)
![Версия](https://img.shields.io/badge/release-v1.0.0-blue)
![Код](https://img.shields.io/badge/code-Apache--2.0-green)
![Документы](https://img.shields.io/badge/docs-CC%20BY%204.0-green)

Исследовательский репозиторий завершённой диссертации о послойном,
механизмном и вычислительно сопоставимом сравнении обратного распространения
ошибки (BP) и режимов предиктивного кодирования (PC) в Torch2PC.

Работа сознательно разделяет утверждения, которые нельзя заменять друг другом:

1. близость конечного поведения;
2. близость внутренних градиентов и представлений;
3. вычислительную стоимость и локализацию этой стоимости;
4. допустимость замены оставшегося канонического вычисления относительно
   требуемого ответа;
5. распознаваемость такой допустимости до действия;
6. экономическую целесообразность решения при полном учёте стоимости.

Финальный текст диссертации находится в [`thesis/`](thesis/). Нормативные
значения терминов заданы в [глоссарии](docs/glossary.md), текущий итог — в
[`STATUS.md`](STATUS.md), а последующая исследовательская программа — в
[`ROADMAP.md`](ROADMAP.md).

## Статус v1.0.0

Научный текст закрыт после независимой пост-рефакторинговой проверки T24.
Зафиксированная научная точка закрытия:

```text
T24_COMMIT=9d45c897d35225fd541aa1b96aeed7fa7e945531
T24_TREE=44575ea3aced7c76633aa05f6ac22b89a20c615f
T24_MERGE=3cd892a62bce947886214fa887bde64748b5bf33
T24_POST_MERGE_TREE_IDENTITY=PASS
THESIS_STATUS=DEFENSE_READY_WITH_EXPLICIT_EXTERNAL_VALIDITY_BOUNDARIES
```

Exact-commit assurance T24 завершился результатом **1732 passed, 8 skipped**;
диссертация собирается в **99 страниц** без overfull boxes, неопределённых
ссылок/цитат и незавершённых cross-reference rerun warnings. Эти числа относятся
к точке T24; релизный manifest дополнительно связывает конкретный тег `v1.0.0`
с его source commit/tree и SHA-256 опубликованных assets.

## Исследовательские вопросы и финальные статусы

Машиночитаемая трассировка хранится в
[`thesis/data/thesis_traceability.json`](thesis/data/thesis_traceability.json).

| RQ | Содержание | Итог |
|---|---|---|
| RQ1 | Когда PC-режимы близки к BP по поведению и внутренней динамике? | C01–C02 `supported` |
| RQ2 | Где возникает вычислительная стоимость и сохраняют ли альтернативные точные организации требуемую эквивалентность/ресурсный допуск? | C03–C06 `supported`; C07 `descriptive` |
| RQ3 | Можно ли до штатного завершения распознать допустимое раннее действие и получить положительную экономию? | C08 `supported`; C09 `rejected`; C10–C11 `not_tested` |

Ключевая эпистемическая граница RQ3: QWake-FP показал информационную
осуществимость на зарегистрированной калибровочной поверхности, но не
экономическую состоятельность при замороженном полном учёте стоимости решения.
Отрицательный C09 **не** переопределяет C10: добавочная стоимость минимального
распознавателя в этой работе не измерялась.

## Теоретическая рамка

- **PC-TREF** — отдельная task-relative рамка эквивалентности и достаточности;
- **PC-CATM** — отдельный связанный механизмный диагностический уровень;
- **QWake-PC** — общая архитектура управления остаточным вычислением;
- **QWake-FP** — проверенная в работе ограниченная реализация для FixedPred.

В QWake-FP раннее действие не означает «никакого дальнейшего вычисления».
Зарегистрированный кандидат
`fixedpred_eta1_wavefront_completion_v1` заменяет оставшийся канонический
итеративный suffix ограниченным аналитическим завершением, а
`complete_suffix_stage2_baseline_v1` остаётся точным эталонным/резервным путём.

Положительный C08 основан на правиле `compute_step >= 5`. Поэтому в этой работе
он устанавливает временную границу фиксированного префикса, а не демонстрирует
input-dependent adaptivity и не подтверждает преимущество признаков PC-CATM.

## Основные эмпирические результаты

- Stage 1/2: в зарегистрированной области FixedPred/Strict сохраняют заданную
  поверхность конечного качества относительно BP при различающейся стоимости;
- Stage 3A: FixedPred наблюдаемо ближе к BP по направлению градиента и
  представлениям, чем Strict, при уменьшенной норме ранних градиентов;
- Stage 3B B0: существенная стоимость локализована в `state_inference`;
- `SI-MA0`: `COST-MA0` не пройден, отрицательный результат сохранён;
- `SI-MA1`: калибровка стоимости наблюдателя пройдена; signed residual не
  интерпретируется как отрицательная физическая стоимость;
- B1/B2: точные кандидаты проходят зарегистрированные equivalence gates, но
  получают `reject_or_revise` на отдельном resource continuation screen;
- QWake C2: из 2625 скалярных правил 264 имеют ненулевое покрытие при нуле
  наблюдавшихся dangerous accepts; максимальное зарегистрированное покрытие —
  216/756 (28.57%), включая 108 preterminal записей шага 5 и 108 terminal
  boundary записей шага 6;
- C09: ни одно правило не сочетает ноль наблюдавшихся dangerous accepts,
  ненулевое покрытие и положительную aggregate net saving при полном frozen
  decision-cost accounting.

Ноль наблюдавшихся опасных принятий на конечной calibration surface не является
популяционной гарантией безопасности.

## Сборка диссертации

```bash
make thesis-check
make thesis
```

`make thesis-check` проверяет claim schema, численные сводки, provenance,
терминологический контракт, QWake action semantics и локальную трассировку
C01–C11. `make thesis` после этих проверок генерирует thesis-facing assets и
собирает PDF через XeLaTeX/Biber.

## Релиз

Версия `1.0.0` публикуется как tag-bound release. Релизный pipeline собирает:

```text
torch2pc-layerwise-thesis-1.0.0.zip
torch2pc-layerwise-thesis-1.0.0.zip.sha256
torch2pc-layerwise-thesis-1.0.0.pdf
torch2pc-layerwise-thesis-1.0.0.pdf.sha256
torch2pc-layerwise-thesis-1.0.0.metadata.json
torch2pc-layerwise-thesis-1.0.0.release-manifest.json
```

Manifest фиксирует source commit/tree, SHA-256 source archive и PDF, число
страниц и результаты release/thesis gates. Подробный release contract проверяет
`scripts/check_release_contract.py`.

## Репозиторий

| Каталог | Роль |
|---|---|
| `thesis/` | финальный текст диссертации, claim registry и generated thesis assets |
| `src/torch2pc_thesis/` | исполняемая исследовательская логика и CLI |
| `experiments/` | исторические preregistration/freeze/authorization contracts и lifecycle records |
| `results/` | отслеживаемые агрегированные результаты и компактные evidence packages |
| `docs/` | глоссарий, теория, методология, ADR и исторические протоколы |
| `configs/` | конфигурации Stage 1/2/3 и аппаратные профили |
| `references/` | BibTeX и трассировка литературы без перераспространения PDF |
| `article/` | вторичный пакет будущей статьи; не определяет v1.0.0 thesis release |

Полное описание: [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md).

## Что является историческим

`HYPOTHESES.md`, `PREREGISTRATION.md`, старые Stage/QWake plans, ADR,
authorization/receipt/freeze документы и встроенные в `STATUS.md`/`ROADMAP.md`
point-in-time блоки сохраняют состояние соответствующего этапа. Их старые
`open=false`, `execution closed` и версии образов не следует читать как текущий
статус v1.0.0. Текущий статус всегда задаётся верхним разделом `STATUS.md`, а
финальные научные статусы — claim registry диссертации.

Исторические image IDs вида `torch2pc-layerwise-thesis:0.1.0-...` также не
переименовываются: они являются частью зафиксированного provenance.

## Совместимость с историческими publication contracts

Следующие маркеры сохраняются в README как исторические regression anchors для
ранее опубликованного matched-profiling слоя; они **не** являются текущим
статусом QWake или разрешением нового scientific execution:

```text
matched_profiling_analysis_publication_action_complete=true
matched_profiling_analysis_publication_receipt_frozen=true
results_publication_permitted=true
release_draft_required=false
release_publication_permitted=true
release_publication_complete=true
```

## Лицензирование

- код: Apache License 2.0 — [`LICENSE`](LICENSE);
- диссертация и документация: CC BY 4.0 — [`LICENSE-DOCS`](LICENSE-DOCS);
- сторонние материалы: условия исходных правообладателей — [`NOTICE`](NOTICE).

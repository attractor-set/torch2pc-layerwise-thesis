# Структура репозитория

[English version](PROJECT_STRUCTURE_EN.md)

Репозиторий `v1.0.1` объединяет три разных типа поверхности, которые нельзя
смешивать: **финальный текст диссертации**, **исполняемую исследовательскую
реализацию** и **исторический provenance экспериментов**.

## Карта верхнего уровня

```text
.
├── thesis/                  # финальная RU/EN диссертация и thesis-facing contracts
│   ├── main.tex             # русская точка входа
│   ├── main_EN.tex          # полная английская точка входа
│   ├── chapters/
│   ├── appendices/
│   ├── frontmatter/
│   ├── data/                # C01–C11, verified summaries, traceability
│   └── generated/           # формируется локально, не является source of truth
├── src/torch2pc_thesis/     # исполняемая исследовательская логика и CLI
├── tests/                   # unit/correctness/integration regression surface
├── configs/                 # Stage 1/2/3 и аппаратные конфигурации
├── experiments/             # planned/frozen/completed lifecycle и authorization records
├── results/                 # агрегированные результаты и compact evidence packages
├── docs/                    # теория, методология, глоссарий, ADR и протоколы
├── references/              # BibTeX и трассировка источников
├── article/                 # вторичный пакет будущей статьи
├── notebooks/               # analysis-only и historical migration notebooks
├── scripts/                 # validation, provenance, thesis и release tooling
├── requirements/            # CPU/ROCm/dev dependency surfaces
├── external/                # локально привязываемые внешние реализации
├── private/                 # исключённая из публичного scientific claim surface область
└── .github/workflows/       # CI, thesis build и tag-bound release
```

## Авторитетные поверхности v1.0.1

### `thesis/`

Финальный научный нарратив. Основные машинные контракты:

- `thesis/data/research_claims.json` — зарегистрированные C01–C11;
- `thesis/data/thesis_traceability.json` — связь каждого claim с theory,
  methodology, experiment, results, discussion и conclusion;
- `thesis/data/qwake_c2_verified_summary.json` — thesis-facing QWake C2
  агрегаты с provenance binding;
- `scripts/build_thesis_assets.py` — проверка/рендеринг русских generated assets;
- `scripts/build_thesis_assets_en.py` — английские generated assets из тех же data contracts;
- `scripts/check_thesis_language_congruence.py` — RU/EN структурная и научно-семантическая конгруэнтность;
- `scripts/check_thesis_semantic_contract.py` — терминология, статусы и QWake
  action semantics;
- `scripts/check_thesis_traceability.py` — локальная claim-to-section binding.

`make thesis-check` проверяет научную и двуязычную поверхность без LaTeX;
`make thesis` собирает русский PDF, `make thesis-en` — английский, а
`make thesis-all` — оба представления.

### `src/torch2pc_thesis/`

Каноническая исполняемая реализация исследовательской логики. Ноутбуки не
должны содержать уникальную научную логику, отсутствующую в `src/`.

### `experiments/` и `results/`

`experiments/` хранит жизненный цикл протоколов, freeze/authorization/receipt
артефактов. `results/` содержит отслеживаемые агрегированные результаты и
компактные evidence packages. Исторические execution-control документы
сохраняют состояние своего времени и не являются текущим разрешением на новый
запуск.

### `docs/`

- `glossary.md` / `_EN` — нормативная терминология;
- `pc-tref-*` — task-relative теоретическая рамка;
- `pc-catm-*` — отдельный механизмный диагностический уровень;
- `qwake-*` — архитектура и исторические bounded protocol surfaces;
- `decisions/` — ADR, включая неизменяемые historical decisions;
- `research-log/` — point-in-time исследовательский журнал.

Текущий итог следует читать по `README.md`, `STATUS.md` и финальной
диссертации; исторические protocol/ADR блоки не переписываются после получения
результата.

## Release surface

Tag `v1.0.1` связывается с exact source commit/tree. `scripts/build_release.sh`
создаёт source archive, отдельные `-ru.pdf`/`-en.pdf`, их SHA-256, metadata и
`release-manifest.json`. Один manifest связывает оба языковых документа с одним
source commit/tree. GitHub workflow публикует именно эти assets и не
перезаписывает существующий release.

## Исторические документы

`HYPOTHESES.md`, `PREREGISTRATION.md`, старые Stage/QWake plans, ADR,
`STATUS.md`/`ROADMAP.md` historical ledgers и image IDs вида
`torch2pc-layerwise-thesis:0.1.0-...` сохраняются как provenance. Их версии и
локальные `open/closed` состояния не нормализуются под `v1.0.1` задним числом.

`pyproject.toml` и `src/torch2pc_thesis/__init__.py` входят в зафиксированные
научные runtime-контуры QWake и поэтому сохраняют историческую package version
`0.1.0` и зарегистрированные SHA-256 identities. Версия публикационного релиза
репозитория определяется отдельным `RELEASE_VERSION`, `CITATION.cff` и тегом;
научный runtime нельзя переписывать только ради синхронизации номера релиза.

## Правило расширения после v1.0.1

Новая научная работа не продолжает старый claim ID автоматически:

```text
new question
-> preregistered protocol / new claim identifier
-> immutable source + environment binding
-> authorized execution
-> preserved evidence
-> independent verification
-> bounded claim decision
-> optional dissertation/article successor
```

В частности, будущая проверка C10 или новая confirmatory surface должна иметь
новый protocol ID и не переопределяет C09/C11 текущей диссертации.

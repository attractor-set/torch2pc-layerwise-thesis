# Журнал изменений

[English version](CHANGELOG_EN.md)

## [0.1.0] - Первый коммит

### Добавлено

- русскоязычный исследовательский репозиторий;
- нейтральные принципы формулирования выводов;
- предварительная спецификация анализа;
- C0/C1 вместо неоднозначных H0/H1;
- запрет test для smoke и pilot;
- обязательный pilot-freeze перед final;
- уникальные `run_id` для повторов;
- append-only реестр;
- сохранение split indices и SHA-256;
- строгий deterministic mode;
- pilot grid для FixedPred и Strict;
- exact sign-flip, effect size и equivalence utilities;
- контейнерная Ubuntu/ROCm-среда;
- тесты и статические проверки;
- immutable source revision label в Docker-образе;
- `environment-lock.json` с hashes code/config, image ID, container packages и host state;
- блокировка повторного успешного final-запуска одной code/config/seed комбинации;
- per-sample prediction artifacts с исходными индексами;
- проверка полноты pilot matrix и validation-only selection на FashionMNIST;
- парный confirmatory report с minimum-pair gate, Holm correction и equivalence CI;
- документ угроз валидности;
- успешные проверки Ruff, Mypy, MkDocs, XeLaTeX и pdfLaTeX.

### Ограничения

- Docker/ROCm runtime еще не выполнен;
- commit Torch2PC не закреплен;
- диагностический executor реализован частично;
- эмпирические результаты отсутствуют.

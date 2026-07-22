# Запрос выполнения описательного анализа Stage 3B

[English version](STAGE3B-MATCHED-DESCRIPTIVE-ANALYSIS-EXECUTION-REQUEST_EN.md)

## Статус

```text
request_id=stage3b-matched-descriptive-analysis-execution-request-v1
request_frozen=true
execution_authorization_present=false
analysis_execution_permitted=false
analysis_execution_performed=false
analysis_results_present=false
results_publication_permitted=false
release_publication_permitted=false
```

Этот документ описывает **запрос**, а не допуск. Он не даёт права читать
числовые значения запечатанных доказательных материалов через анализатор,
создавать выходной пакет или публиковать результаты.

## Зафиксированные идентичности

Запрос связан с:

- hardening-base commit
  `70d6c3ca971415f57805dbf9b2ed4bbb80b2d873`;
- evidence tag `stage3b-matched-profiling-evidence-v1` и commit
  `21ddfb8840674871f0b9d888b36397f5cf0e111b`;
- profiling source commit
  `e1dcfb26823e1191b98d2aa2a598499b13197583`;
- frozen protocol SHA-256
  `074510f1212f1eceb41da8b42ab52f1fd9d816c3901f2a3b8e4e7afec59a3209`;
- analysis-core SHA-256
  `0e9f55fc337b7870923a087308f370afc54bdce97501ce462c1033062a322462`;
- всеми девятью SHA-256 запечатанного входного пакета, включая сжатый
  поток локальности.

Машиночитаемый источник:

`experiments/frozen/stage3b-matched-descriptive-analysis-execution-request-v1/request.json`.

## Запрошенное выполнение

Запрошен максимум один read-only запуск после отдельного допуска. Допуск обязан:

1. ссылаться на точный `request_digest`;
2. зафиксировать runtime identity и точный `generated_at_utc`;
3. проверить неизменность protocol и analysis core;
4. проверить SHA-256 всех входов до и после выполнения;
5. подтвердить отсутствие выходного каталога;
6. запретить повторный запуск;
7. оставить публикацию закрытой после создания результатов.

## Выходной контракт

Единственный запрошенный каталог:

`results/stage-3/analysis/matched/stage3b-matched-descriptive-analysis-70d6c3c-v1`.

До авторизованного выполнения он не должен существовать. Успешное выполнение
должно атомарно создать ровно 18 верхнеуровневых файлов, уже перечисленных во
frozen protocol и `request.json`. Частичный или дополнительный набор закрывает
выполнение ошибкой.

## Следующий gate

Следующий отдельный PR может содержать только runtime preflight и
машиночитаемую authorization. До его merge запрещены:

- вызов sealed-evidence engine;
- создание выходного каталога;
- вычисление сравнительных метрик;
- выбор кандидата;
- публикация draft release;
- переход к `EX-IF0`.

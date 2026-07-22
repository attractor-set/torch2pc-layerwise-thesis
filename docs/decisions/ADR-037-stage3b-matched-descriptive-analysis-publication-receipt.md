# ADR-037: фиксация квитанции публикации описательного анализа этапа 3B

[English version](ADR-037-stage3b-matched-descriptive-analysis-publication-receipt_EN.md)

## Статус

Принято.

## Контекст

Публикационный барьер из ADR-036 был выполнен по отдельному тегу
`stage3b-matched-descriptive-analysis-publication-v1`. Повторный [запуск](../glossary.md#term-run)
конвейера `29955946081` успешно завершился на коммите
`d1e7574280bf0122cbecbb5b64ff2c66c0851907`, который входит в историю
`main`. Выпуск `stage3b-matched-profiling-evidence-v1` опубликован как
нечерновой, не предварительный и изменяемый; обязательные артефакты публикации
присутствуют с зафиксированными контрольными суммами.

## Решение

Сохранить точную квитанцию после действия в каталоге
`experiments/frozen/stage3b-matched-descriptive-analysis-publication-receipt-v1/`
вместе с `SHA256SUMS`. Квитанция связывает:

- тег публикации и коммит;
- коммит `main` на момент фиксации;
- успешный запуск GitHub Actions;
- идентификатор выпуска, время публикации и состояние;
- полный перечень артефактов выпуска и конвейера;
- границу допустимых утверждений после публикации.

Фиксация квитанции переводит следующие состояния в `true`:

```text
matched_profiling_analysis_publication_action_complete=true
matched_profiling_analysis_publication_receipt_frozen=true
results_publication_permitted=true
release_publication_permitted=true
release_publication_complete=true
```

Она не открывает `EX-IF0`, [выполнение](../glossary.md#term-execution)
рекурсивных агрегатов, утверждения о превосходстве, активацию политики или
тестовую выборку.

## Последствия

Этап публикации описательного анализа завершён и воспроизводимо связан с
удалённым [происхождением](../glossary.md#term-provenance). Следующий допустимый
переход — отдельная фиксация протокола `EX-IF0`; эта ADR не является таким
протоколом и не разрешает его выполнение.

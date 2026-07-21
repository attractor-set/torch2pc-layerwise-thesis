# Дорожная карта

[English version](ROADMAP_EN.md)

Дорожная карта отделяет завершённые этапы от разрешённой и заблокированной
работы. Каждый переход требует проверенных артефактов, сохранения границ
утверждений и отдельного решения о допуске.

## Этапы 1–10 — завершены

Завершены инфраструктура и пилот, Stage 1/2, Stage 3A, доказательные материалы
Stage 3B B0 и статистический и инженерный анализ B0. Тестовая выборка
оставалась закрытой.

## Этап 11 — Scenario A и исходная теория — завершён

`ADR-012` закрепил PC-TREF Balanced Core, PC-CATM и Scenario A. `ECZ` имеет
единственное значение `Error-Cancellation Zone`; B0 остаётся неизменяемой
базовой линией.

## Этап 12 — проверки валидности и `SI-MA0` — завершён

Завершены проверки shortcut/equivalence, невмешательства наблюдателя,
детерминированные механизмные контроли и `SI-MA0`. Проверки `REC`, `OBS`,
`VER` и `CMP` прошли, `COST` не прошёл; общий отрицательный итог сохранён.

## Этап 13 — `SI-MA1` — завершён

Завершены предварительная регистрация, реализация, подтверждающее выполнение
и итоговое решение `SI-MA1`. На десяти `model_seed` и 180 сопоставленных
блоках получено `CAL-COST-MA1=true`, `SI-MA1=pass`. Результат `SI-MA0`
не изменён; стоимость будущего оценивателя `ECZ` исключена.

## Этап 14 — теоретическая фиксация перед B1/B2 — завершён

Операциональная семантика PC-TREF/PC-CATM, regret, контракты норм,
`precision-masked zero`, вектор стоимости и разделение затрат опубликованы
под `ADR-013`.

## Этап 15 — предварительная регистрация B1/B2 — завершён

Зафиксированы B1 `isolated_layer_vjp`, B2 `composite_vjp`, общий обзор и
`ADR-014`. Публикационный тег: `stage3b-b1-b2-prereg-v1`. Варианты B2
`block`/`chunk` не входят в этот контракт и требуют отдельной предварительной
регистрации.

## Этап 16 — точные кандидаты и [сопоставленное профилирование](docs/glossary.md#term-matched-profiling) — evidence сохранён, анализ закрыт

Завершено:

- B1 реализован и запечатан как confirmatory `EQ-B1` на 120/120 парах;
- B2 реализован и прошёл engineering smoke на 12/12 тройках и 24/24
  сравнениях;
- реализован candidate-aware matched-profiling runner;
- зафиксировано fail-closed требование confirmatory B2 перед production launch;
- предварительно зарегистрирован confirmatory B2 на 120 троек и 240 сравнений;
- выполнен и запечатан confirmatory B2: 120/120 троек, 240/240 сравнений, `EQ-B2-CONFIRMATORY=pass`, derived `EQ-B2`; evidence сохранён в `stage3b-b2-confirmatory-63885e5-v1`.

Текущая граница:

```text
scientific_admission=open
candidate_aware_runner=complete
b2_confirmatory_decision=pass_sealed
b2_confirmatory_request_frozen=true
b2_confirmatory_admission=present
matched_profiling_request_refrozen=true
matched_profiling_request_refresh_required=false
matched_profiling_execution_open=false
matched_profiling_execution_complete=true
matched_profiling_runtime_validation=valid
matched_profiling_evidence=sealed
matched_profiling_analysis_open=false
runtime_authorization=issued_consumed
measurements_allowed=false
results_publication_permitted=false
release_draft_required=true
release_publication_permitted=false
full_stage3b_campaign_complete=false
```

Новый версионированный `v2` request/manifest freeze со ссылками на sealed
admissions B1 и B2 завершён. Immutable image, ROCm/float32 preflight,
authorization и dry-run прошли. Все 288 ячеек и 96 matched blocks выполнены без
failures и retries, runtime validation прошла, а compact evidence package
запечатан и перенесён в репозиторий.

Оставшийся переход внутри этапа 16:

1. merge evidence-preservation PR и зелёный CI;
2. draft release `stage3b-matched-profiling-evidence-v1` с sealed evidence и
   артефактами запуска;
3. отдельный analysis-opening checkpoint;
4. описательный paired analysis B0/B1/B2 и формальное решение
   `retain / conditional / reject`.

До analysis-opening запрещены сравнительные утверждения, публикация и переход к
`EX-IF0`. Отрицательные и смешанные результаты сохраняются.

## Этап 17 — `EX-IF0`, пассивная диагностика и `A11-OFF0`

Только после завершения и фиксации сопоставленного профилирования выбрать и
зафиксировать допустимую точную реализацию до создания меток. Затем собирать
пассивные представления PC-CATM и из идентичного `snapshot` создавать
нейтральные к политике ветви `stop`, `native_one` и `exact_one`. По `exact-reference`
формируются `oracle skip regret`, `oracle`-запас $M^*$ и `one-step` граница
достаточности; `pre-action` признаки сохраняются отдельно и не получают права
управлять выполнением. Также сохраняются полезность, regret решения, временная
история, стоимость признаков, переходы и происхождение. Независимая единица —
`model_seed`; тестовая выборка закрыта.

## Этап 18 — `A11-OFF1`, предиктор (`predictor`), точная проверка и теневой режим (`shadow`) `QWake-PC`

- провести офлайн-отсев вложенных представлений, оценивателей границы,
  `first-order` горизонтов, признаков и порогов по regret, опасным пропускам и
  полному вектору стоимости;
- до подтверждающего доступа зафиксировать представление, метки, разбиение,
  правило Парето и резервный переход;
- отдельно предварительно зарегистрировать предиктор с группировкой по
  `model_seed`;
- выполнить контрфактическую точную проверку из идентичного состояния;
- начать с теневого режима;
- регистрировать гистерезис как пороги остановки и пробуждения, требуемую
  устойчивость подтверждения и аварийный `fallback_exact`;
- разрешать активное распределение только после проверок безопасности и
  сквозной стоимости.

## Этап 19 — итоговая фиксация и тестовая оценка

Зафиксировать реализацию, признаки, пороги, предиктор, резервный переход и
статистический план. Только затем разрешить однократную итоговую оценку на
тестовой выборке.

## Этап 20 — диссертация и статья

Объединить Stage 1/2, Stage 3A, B0, `SI-MA0`, `SI-MA1`, B1/B2 и доступные
результаты Scenario A. Невыполненные расширения обозначить как будущую работу.

## Граница после магистерской работы — перспективная PhD-линия

После завершения текущего критического пути возможна отдельная программа
`QWake-SPC`: переход от
[спайкоподобной управляющей динамики](docs/glossary.md#term-spike-like-control-dynamics)
QWake-PC к нативным spikes, spike-native переносу ошибок, локальному обучению и
нейроморфной проверке. Эта программа не является этапом 21, не открывает
выполнение и не изменяет критерии завершения магистерской работы.

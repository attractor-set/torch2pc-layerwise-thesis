# Статус исследования

[English version](STATUS_EN.md)

Состояние зафиксировано после полного validation-only pilot. Наличие успешных
контролей не трактуется как универсальное доказательство эквивалентности, а
pilot не используется как итоговый test-результат.

| Компонент | Наблюдаемый статус |
|---|---|
| Структура репозитория | Создана и статически проверена |
| Test isolation | Реализована; в pilot `test_evaluated=false` |
| Split persistence и SHA-256 | Реализованы и проверены для pilot split |
| Torch2PC commit | Зафиксирован: `00c6c50ee3540537bbb56ab2b6567b541f42b093` |
| Docker/ROCm runtime | Проверен на целевом Ubuntu-хосте и RX 7700 XT |
| Структурная проверка поправки | Выполнена для закрепленного `TorchSeq2PC.py` |
| C0 Exact/BP | Пройден на CPU float64 и GPU float32 |
| C1 FixedPred/Exact | Пройден на CPU float64 и GPU float32 |
| Validation-only pilot | 96/96 terminal-ячеек, 0 failed, test не вычислялся |
| Pilot selection | FixedPred `eta=0.1`, `n=10`; Strict `eta=0.05`, `n=20` |
| Компактные pilot-наблюдения | Требуется сгенерировать `pilot_observations.csv` до нового lock |
| Pilot freeze | Еще не создан |
| Final | Заблокирован до нового environment lock, C0/C1 и pilot-freeze |
| CKA/RSA/robustness executor | Запланирован, реализован частично |
| Подтверждающие результаты диссертации | Отсутствуют до final |

# Жизненный цикл эксперимента

[English version](README_EN.md)

Каталог сохраняет lifecycle научных процедур: planned contracts,
freeze/authorization/receipt packages, completed summaries и append-only
registry. Завершение процедуры не означает истинность гипотезы.

Для исторических Stage/QWake веток локальные `open/closed` поля относятся к
моменту соответствующего документа. Они **не являются текущим разрешением на
новый запуск после `v1.0.0`**.

Новый scientific execution после диссертационного closure требует нового
protocol/claim identifier и отдельного authorization boundary. C1/C2 исходной
QWake цепочки не перезапускаются, а C3 не открывается ретроспективно.

`registry.csv`, где применимо, остаётся append-only: одна попытка сохраняет
уникальный `run_id`, terminal outcome и происхождение; предыдущие записи не
перезаписываются.

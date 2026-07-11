# ADR-003: Macro F1 как основная метрика выбора

[English version](ADR-003-primary-metric_EN.md)

Статус: принято до pilot.

Macro F1 используется для выбора по validation и основного final comparison.
Accuracy публикуется как вторичная метрика. Решение не предполагает, что macro
F1 обнаружит различия; оно фиксирует правило выбора до test.

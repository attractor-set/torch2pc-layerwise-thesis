# Внешние исходные коды

[English version](README_EN.md)

Torch2PC клонируется в этот каталог на этапе `make prepare`. Каталог исключен
из Git.

Перед pilot/final необходимо:

1. выполнить аудит поправки;
2. сохранить полный commit SHA;
3. перенести commit в `configs/base.yaml`;
4. запретить автоматическое обновление checkout.

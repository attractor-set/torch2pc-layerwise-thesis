# Система конфигураций

[English version](README_EN.md)

Конфигурация собирается последовательно:

```text
base.yaml
-> hardware/<profile>.yaml
-> stages/<stage>.yaml
-> methods/<method>.yaml
-> experiments/<optional-experiment>.yaml
-> переопределения CLI
```

Более поздние значения переопределяют более ранние. Каждый запуск сохраняет
полностью разрешенную конфигурацию и ее SHA-256.

Пример:

```bash
torch2pc-thesis resolve \
  --stage final \
  --method fixedpred \
  --dataset FashionMNIST \
  --seed 3 \
  --output results/resolved/example.yaml
```

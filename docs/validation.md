# Проверка репозитория

[English version](validation_EN.md)

Проверки выполняются из текущего коммита Git. Статические отчёты с результатами
проверок не хранятся как постоянное утверждение в корне репозитория, поскольку
после изменения исходного кода они перестают описывать текущее состояние.

## Локальная проверка

```bash
source .venv/bin/activate
python3 -m ruff check src tests scripts/*.py
python3 -m mypy src
python3 -m pytest -q
python3 scripts/check_epistemic_language.py
python3 scripts/check_language_structure.py
python3 scripts/check_glossary_usage.py
python3 scripts/check_local_links.py
bash scripts/validate_repository.sh
```

## Проверка в CI

GitHub Actions выполняет те же проверки в чистом окружении с зависимостями,
ограниченными файлами `requirements/lock-dev.txt` и
`requirements/torch-cpu.txt`.

Зелёный CI подтверждает прохождение проверок для конкретного коммита. Он не
подтверждает научные гипотезы и не заменяет Docker/ROCm, C0/C1, пилотное или
итоговое [выполнение](glossary.md#term-execution).

## Релизные сведения

`scripts/build_release.sh` создаёт архив из `git archive` и записывает рядом:

- SHA-256 архива;
- версию проекта;
- полный коммит Git;
- время создания метаданных.

Результаты экспериментов времени выполнения должны иметь собственные
манифесты и связь с `environment-lock.json`.

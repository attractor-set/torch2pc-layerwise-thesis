# Исходники диссертации

[English version](README_EN.md)

`main.tex` является нейтральным LaTeX-каркасом, а не официальным шаблоном
кафедры МИФИ. Текст включает нейтральные аннотации, список сокращений,
основные главы и приложение по воспроизводимости; перед сдачей титульная
страница и оформление заменяются на утвержденный шаблон.

Таблицы и рисунки подключаются из `../results/`. Численные значения не следует
переписывать вручную, если существует автоматически сформированная таблица.

Сборка:

```bash
make thesis
```

Сборка диссертации использует XeLaTeX и системные шрифты Liberation.

## Dissertation contract and generated assets

Research questions and the claims matrix are stored in
`data/research_claims.json`. The QWake C2 thesis-facing aggregate summary is
stored in `data/qwake_c2_verified_summary.json` and contains frozen source
identities plus independently verified aggregate values; it does not replace
or reinterpret the underlying scientific evidence.

`make thesis` first validates these data files and deterministically renders
the claims/results tables plus `generated/reproducibility_manifest.tex`, then
runs XeLaTeX. Generated `.tex` assets are not committed. The reproducibility
manifest binds the dissertation to tracked Stage 1/2/3 evidence and frozen
QWake identities without copying the full forensic evidence surface into Git.

A data-only validation that does not require LaTeX can be run with:

```bash
make thesis-check
```

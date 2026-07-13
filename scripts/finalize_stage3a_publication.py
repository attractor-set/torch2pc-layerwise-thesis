#!/usr/bin/env python3
"""Finalize Stage 3A publication metadata without changing raw observations."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from typing import Final

AGGREGATOR = '''#!/usr/bin/env python3
"""Aggregate Stage 3 layer-wise probe outputs with seed provenance."""

from __future__ import annotations

import argparse
from pathlib import Path

from torch2pc_thesis.stage3_aggregation import aggregate_tables


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    row_counts = aggregate_tables(args.root, args.output)
    for filename, rows in row_counts.items():
        print(f"{filename}: rows={rows}")


if __name__ == "__main__":
    main()
'''

STATUS_RU = '''# Статус исследования

[English version](STATUS_EN.md)

Stage 1/2 завершены и остаются неизменяемой опубликованной базовой линией.
Диагностическая подкампания **Stage 3A layer-wise diagnostics** завершена;
расширенные линии locality, profiling и acceleration продолжаются отдельно.

| Компонент | Наблюдаемый статус |
|---|---|
| Validation-only pilot | 96/96; test не вычислялся |
| Stage 1 / Stage 2 | 80/80 и 80/80 |
| Stage 2 runtime | `BP ≈ Exact < FixedPred << Strict` |
| Stage 3A same-state probes | 10/10 seeds |
| Stage 3A representation probes | 10/10 seeds |
| Exact–BP numerical controls | 10/10 passed |
| Gradient observations | 2250; cosine определён для 2250/2250 |
| Representation observations | 150; RSA определён для 150/150 |
| Cross-layer CKA observations | 750 |
| Regression suite | 94 passed |
| Test access Stage 3A | validation-only diagnostics; test loader не создавался |
| Расширенный Stage 3 | profiling, locality, exact candidates и approximations ожидают отдельных gates |

## Текущая интерпретация

Stage 3A сформировал подтверждающий послойный evidence-набор для финальных
FashionMNIST checkpoints `lenet_classic`, seeds 0–9. Статистической единицей
остаётся независимо обученная модель; слои, batches и samples являются
повторными наблюдениями внутри seed.

## Следующий шаг

Выполнить парный seed-level статистический анализ, Holm-коррекцию, оценку
эффектов и построение графиков. После публикации Stage 3A можно продолжить
ранее спроектированные locality/profiling и acceleration линии как отдельные
подкампании с собственной provenance chain.
'''

STATUS_EN = '''# Research status

[Русская версия](STATUS.md)

Stage 1/2 are complete immutable published baselines. The **Stage 3A
layer-wise diagnostics** confirmatory subcampaign is complete; the broader
locality, profiling, and acceleration lines remain separate future work.

| Component | Observed status |
|---|---|
| Validation-only pilot | 96/96; test not evaluated |
| Stage 1 / Stage 2 | 80/80 and 80/80 |
| Stage 2 runtime | `BP ~= Exact < FixedPred << Strict` |
| Stage 3A same-state probes | 10/10 seeds |
| Stage 3A representation probes | 10/10 seeds |
| Exact–BP numerical controls | 10/10 passed |
| Gradient observations | 2250; cosine defined for 2250/2250 |
| Representation observations | 150; RSA defined for 150/150 |
| Cross-layer CKA observations | 750 |
| Regression suite | 94 passed |
| Stage 3A test access | validation-only diagnostics; no test loader created |
| Broader Stage 3 | profiling, locality, exact candidates, and approximations remain gated |

## Current interpretation

Stage 3A provides confirmatory layer-wise evidence for final FashionMNIST
`lenet_classic` checkpoints across seeds 0–9. The independently trained model
seed is the statistical unit; layers, batches, and samples are repeated
observations within a seed.

## Next step

Run paired seed-level statistics, Holm correction, effect-size estimation,
and figure generation. Continue locality/profiling and acceleration as
separate subcampaigns with their own provenance chains.
'''

ROADMAP_RU = '''# Дорожная карта

[English version](ROADMAP_EN.md)

## Фазы 1–5 — завершены

1. Research scaffold и preregistration.
2. Controlled environment и validation-only pilot 96/96.
3. Stage 1 confirmatory campaign 80/80.
4. Stage 2 implementation study 80/80.
5. Public release и проверка неавторизованного доступа.

## Фаза 6 — Stage 3 design revision 2 завершена

Закреплены locality/profiling contracts, exact candidates, core
approximations и predict-correct candidates.

## Фаза 7 — Stage 3A layer-wise diagnostics завершена

- same-state gradient probes: seeds 0–9;
- independently trained representation probes: seeds 0–9;
- Exact–BP controls: 10/10 passed;
- опубликованы агрегированные gradient, CKA и RSA evidence-таблицы;
- raw observations сохраняются отдельно от Git.

## Фаза 8 — Stage 3A statistical publication — текущая

- парная статистика по model seed;
- Holm-коррекция внутри заранее определённых семейств;
- effect sizes и интервалы;
- gradient/depth и representation figures;
- evidence tag и replication bundle.

## Фаза 9 — locality и exact execution

Выполнить B0/A0 profiling, затем B1/B2 gates и attribution. Эти эксперименты
не изменяют завершённый Stage 3A diagnostic evidence-набор.

## Фаза 10 — core approximations и predict-correct

C1/C2 и C4/C5 проходят отдельные validation-only screening campaigns с
residual, fallback, non-inferiority и VJP-reduction gates.

## Фаза 11 — расширенный Stage 3 freeze и final

Заморозить выбранные candidates и параметры, создать отдельные execution и
publication states и только после freeze разрешить final test evaluation.

## Фаза 12 — диссертация и статья

Объединить Stage 1/2, Stage 3A diagnostics и последующие locality/acceleration
результаты, подготовить replication bundles и clean-room reproduction.
'''

ROADMAP_EN = '''# Roadmap

[Русская версия](ROADMAP.md)

## Phases 1–5 — complete

Research scaffold, controlled environment and 96/96 pilot, Stage 1 80/80,
Stage 2 80/80, and the public release are complete.

## Phase 6 — Stage 3 design revision 2 complete

The locality/profiling contracts, exact candidates, core approximations, and
predict-correct candidates are specified.

## Phase 7 — Stage 3A layer-wise diagnostics complete

- same-state gradient probes for seeds 0–9;
- independently trained representation probes for seeds 0–9;
- Exact–BP controls passed for 10/10 seeds;
- aggregate gradient, CKA, and RSA evidence tables published;
- raw observations retained outside Git.

## Phase 8 — Stage 3A statistical publication — current

Run paired model-seed statistics, within-family Holm correction, effect-size
and interval estimation, figure generation, evidence tagging, and replication
bundle publication.

## Phase 9 — locality and exact execution

Run B0/A0 profiling, then B1/B2 numerical gates and attribution. These
experiments remain separate from the completed Stage 3A diagnostic evidence.

## Phase 10 — core approximations and predict-correct

Run C1/C2 and C4/C5 as separate validation-only screening campaigns with
residual, fallback, non-inferiority, and VJP-reduction gates.

## Phase 11 — extended Stage 3 freeze and final

Freeze selected candidates and parameters, preserve distinct execution and
publication states, and enable final test evaluation only after the freeze.

## Phase 12 — thesis and article

Integrate Stage 1/2, Stage 3A diagnostics, and later locality/acceleration
results; publish replication bundles and complete clean-room reproduction.
'''

COMPLETE_RU = '''# Завершение подтверждающей Stage 3A layer-wise кампании

[English version](STAGE3-LAYERWISE-CONFIRMATORY-COMPLETE_EN.md)

## Область исполнения

- Dataset: FashionMNIST
- Architecture: `lenet_classic`
- Model seeds: 0–9
- Methods: BP, Exact, FixedPred, Strict
- Checkpoint: final
- Same-state reference: парный BP checkpoint
- Representation comparison: независимо обученные парные checkpoints
- Environment: controlled ROCm Docker image

## Контрольные рубежи

- same-state seeds: 10/10;
- representation seeds: 10/10;
- Exact–BP numerical controls: 10/10 passed;
- gradient metric rows: 2250;
- gradient summary rows: 450;
- representation metric rows: 150;
- cross-layer CKA rows: 750;
- gradient cosine defined: 2250/2250;
- representation RSA defined: 150/150;
- artifact hashes: PASS;
- unit tests: 7 passed;
- full regression suite: 94 passed;
- Mypy: PASS.

## Статистическая единица

Статистической единицей является независимо обученная модель, заданная
`model_seed`. Layers, parameters, batches, samples и layer pairs являются
повторными наблюдениями внутри seed и не считаются независимыми репликациями.

## Provenance

Raw observations созданы source commit, записанным в
`results/stage3/layerwise/confirmatory/provenance/SOURCE_COMMIT`.

Исходный `COMPOSE_RESOLVED.yaml` сохранён неизменным. Обнаруженное различие
между его устаревшим `SOURCE_GIT_COMMIT` и фактическим image revision описано
в `provenance/CORRECTION.md`.

Агрегированные representation tables получили `model_seed` из sibling
`metadata.json`; migration repair по canonical `source_file` path не менял
raw activations, gradient/CKA/RSA values, layer/sample/checkpoint selection или
numerical gates.

## Следующая фаза

Evidence готов для парного seed-level статистического анализа, коррекции
множественных сравнений, оценки эффектов, depth-trend анализа и построения
рисунков.
'''

COMPLETE_EN = '''# Stage 3A Layer-wise Confirmatory Completion

[Русская версия](STAGE3-LAYERWISE-CONFIRMATORY-COMPLETE.md)

## Execution scope

- Dataset: FashionMNIST
- Architecture: `lenet_classic`
- Model seeds: 0–9
- Methods: BP, Exact, FixedPred, Strict
- Checkpoint: final
- Same-state reference: paired BP checkpoint
- Representation comparison: independently trained paired checkpoints
- Environment: controlled ROCm Docker image

## Completion gates

- same-state seeds completed: 10/10;
- representation seeds completed: 10/10;
- Exact–BP numerical controls passed: 10/10;
- gradient metric rows: 2250;
- gradient summary rows: 450;
- representation metric rows: 150;
- cross-layer CKA rows: 750;
- gradient cosine defined: 2250/2250;
- representation RSA defined: 150/150;
- artifact hashes verified: PASS;
- unit tests: 7 passed;
- full regression suite: 94 passed;
- Mypy checks: PASS.

## Statistical unit

The independently trained model seed is the statistical unit. Layers,
parameters, batches, samples, and layer pairs are repeated observations within
a seed and are not independent replicates.

## Provenance

Raw observations were generated by the source commit recorded in
`results/stage3/layerwise/confirmatory/provenance/SOURCE_COMMIT`.

The original `COMPOSE_RESOLVED.yaml` is preserved unchanged. The stale
`SOURCE_GIT_COMMIT` value in that snapshot and the actual image revision are
documented in `provenance/CORRECTION.md`.

Aggregated representation tables receive `model_seed` from sibling
`metadata.json`. The migration repair based on canonical `source_file` paths
did not change raw activations, gradient/CKA/RSA values, layer/sample/checkpoint
selection, or numerical gates.

## Next phase

The evidence is ready for paired seed-level statistics, multiplicity
correction, effect-size estimation, depth-trend analysis, and figure
generation.
'''

README_RU_STAGE3 = '''## Stage 3A: послойная диагностика завершена

Подтверждающая validation-only подкампания выполнена для FashionMNIST,
`lenet_classic`, seeds 0–9. Для каждого seed завершены same-state gradient
probes и comparison independently trained representations; Exact–BP controls
пройдены 10/10. Опубликованы 2250 gradient observations, 150 corresponding
CKA/RSA observations и 750 cross-layer CKA observations.

Stage 3A не является завершением всего расширенного Stage 3. Locality,
profiling, exact execution, adaptive stopping, periodic refresh и
predict-correct остаются отдельными подкампаниями с собственными gates и
provenance chains. Текущий статус: [STATUS.md](STATUS.md).
'''

README_EN_STAGE3 = '''## Stage 3A: layer-wise diagnostics complete

The validation-only confirmatory subcampaign covers FashionMNIST,
`lenet_classic`, and seeds 0–9. Same-state gradient probes and independently
trained representation comparisons are complete for every seed; all 10
Exact–BP controls passed. Published evidence contains 2250 gradient
observations, 150 corresponding CKA/RSA observations, and 750 cross-layer CKA
observations.

Stage 3A does not complete the broader Stage 3. Locality, profiling, exact
execution, adaptive stopping, periodic refresh, and predict-correct remain
separate gated subcampaigns with their own provenance chains. See
[STATUS_EN.md](STATUS_EN.md).
'''

CORRECTION_TEMPLATE = '''# Stage 3A provenance correction note

The confirmatory raw observations were generated by controlled image revision
`{execution_commit}`, as recorded by both `SOURCE_COMMIT` and
`IMAGE_INSPECT.json` (`SOURCE_GIT_COMMIT` / OCI revision).

The preserved `COMPOSE_RESOLVED.yaml` snapshot contains the older value
`6d66b0a6f82c30c4fb8eca6247383ca13e0636a2` for `SOURCE_GIT_COMMIT`. This was
a stale host-side Compose variable captured during provenance export; it does
not match the revision embedded in the container image that executed the
probes.

The original Compose snapshot is retained unchanged. For interpretation of
execution provenance, the image metadata and `SOURCE_COMMIT` are authoritative.
This correction note changes no raw observations, metrics, checkpoints, or
analysis decisions.
'''

CONFIRMATORY_ROOT: Final[Path] = Path(
    "results/stage3/layerwise/confirmatory"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--execution-commit", default=None)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def replace_section(text: str, heading: str, next_heading: str, body: str) -> str:
    pattern = re.compile(
        rf"^{re.escape(heading)}.*?(?=^{re.escape(next_heading)})",
        flags=re.MULTILINE | re.DOTALL,
    )
    replacement = body.rstrip() + "\n\n"
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError(f"cannot replace section {heading!r}")
    return updated


def update_readme(path: Path, *, english: bool) -> None:
    text = path.read_text(encoding="utf-8")
    if english:
        text = text.replace(
            "the maintained regression suite contains **63 passing tests**",
            "the maintained regression suite contains **94 passing tests**",
        )
        if "## Stage 3: design-ready" in text:
            text = replace_section(
                text,
                "## Stage 3: design-ready",
                "## Pilot evidence export",
                README_EN_STAGE3,
            )
    else:
        text = text.replace(
            "Stage%203%20design--ready",
            "Stage%203A%20diagnostics%20complete",
        )
        text = text.replace(
            "regression suite после maintenance: **63 passed**",
            "regression suite после maintenance: **94 passed**",
        )
        text = replace_section(
            text,
            "## Stage 3: design-ready",
            "## Контрольные проверки",
            README_RU_STAGE3,
        ) if "## Stage 3: design-ready" in text else text
    path.write_text(text, encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def regenerate_manifest(root: Path) -> None:
    manifest = root / "SHA256SUMS"
    paths = sorted(
        path for path in root.rglob("*") if path.is_file() and path != manifest
    )
    lines = [f"{sha256(path)}  {path.as_posix()}" for path in paths]
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def expected_files(repo: Path) -> dict[Path, str]:
    return {
        repo / "scripts/aggregate_stage3_layerwise.py": AGGREGATOR,
        repo / "STATUS.md": STATUS_RU,
        repo / "STATUS_EN.md": STATUS_EN,
        repo / "ROADMAP.md": ROADMAP_RU,
        repo / "ROADMAP_EN.md": ROADMAP_EN,
        repo / "experiments/planned/STAGE3-LAYERWISE-CONFIRMATORY-COMPLETE.md": COMPLETE_RU,
        repo / "experiments/planned/STAGE3-LAYERWISE-CONFIRMATORY-COMPLETE_EN.md": COMPLETE_EN,
    }


def main() -> None:
    args = parse_args()
    repo = args.repo_root.resolve()
    confirmatory = repo / CONFIRMATORY_ROOT
    source_commit_path = confirmatory / "provenance/SOURCE_COMMIT"
    execution_commit = args.execution_commit or source_commit_path.read_text(
        encoding="utf-8"
    ).strip()

    correction = CORRECTION_TEMPLATE.format(execution_commit=execution_commit)
    files = expected_files(repo)
    files[confirmatory / "provenance/CORRECTION.md"] = correction

    if args.check:
        mismatches = []
        for path, expected in files.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                mismatches.append(path)
        if mismatches:
            raise SystemExit(
                "publication files require finalization:\n"
                + "\n".join(str(path) for path in mismatches)
            )
        return

    update_readme(repo / "README.md", english=False)
    update_readme(repo / "README_EN.md", english=True)

    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    regenerate_manifest(confirmatory)
    print(f"Stage 3A publication finalized for execution commit {execution_commit}")


if __name__ == "__main__":
    main()

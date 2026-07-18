from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RU_DESIGN = ROOT / "docs/cheap-diagnostic-certificates.md"
EN_DESIGN = ROOT / "docs/cheap-diagnostic-certificates_EN.md"
RU_ADR = (
    ROOT
    / "docs/decisions/ADR-015-stage3b-cheap-diagnostic-certificates.md"
)
EN_ADR = (
    ROOT
    / "docs/decisions/ADR-015-stage3b-cheap-diagnostic-certificates_EN.md"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_cheap_certificate_documents_are_bilingual() -> None:
    ru_design = _read(RU_DESIGN)
    en_design = _read(EN_DESIGN)
    ru_adr = _read(RU_ADR)
    en_adr = _read(EN_ADR)

    assert "cheap-diagnostic-certificates_EN.md" in ru_design
    assert "cheap-diagnostic-certificates.md" in en_design
    assert "ADR-015-stage3b-cheap-diagnostic-certificates_EN.md" in ru_adr
    assert "ADR-015-stage3b-cheap-diagnostic-certificates.md" in en_adr

    language_map = _read(ROOT / "docs/language-map.csv")
    assert (
        "docs/cheap-diagnostic-certificates.md,"
        "docs/cheap-diagnostic-certificates_EN.md,required"
        in language_map
    )
    assert (
        "docs/decisions/ADR-015-stage3b-cheap-diagnostic-certificates.md,"
        "docs/decisions/ADR-015-stage3b-cheap-diagnostic-certificates_EN.md,"
        "required"
        in language_map
    )


def test_certificate_status_is_separate_from_mechanism_label() -> None:
    for text in (_read(RU_DESIGN), _read(EN_DESIGN)):
        assert '"mechanism_label": "ECZ"' in text
        assert '"certificate_status": "certified"' in text
        assert "`exact`" in text
        assert "`certified`" in text
        assert "`abstained`" in text
        assert "`invalid`" in text


def test_ecz_and_ncz_certificates_remain_asymmetric() -> None:
    ru = _read(RU_DESIGN)
    en = _read(EN_DESIGN)

    assert "первого надёжного свидетельства" in ru
    assert "верхняя граница для всех релевантных каналов" in ru
    assert "Отсутствие обнаруженного активного канала" in ru

    assert "first reliable activity witness" in en
    assert "upper bound for every relevant channel" in en
    assert "Failure to find an active channel" in en


def test_certificates_have_no_action_permission() -> None:
    for text in (
        _read(RU_DESIGN),
        _read(EN_DESIGN),
        _read(RU_ADR),
        _read(EN_ADR),
    ):
        assert "action_permission" in text
        assert "NCZ`" in text
        assert "ECZ`" in text

    assert "`NCZ` не означает `stop`" in _read(RU_DESIGN)
    assert "`ECZ` не означает `continue` или локальный проход" in _read(RU_DESIGN)
    assert "`NCZ` does not mean `stop`" in _read(EN_DESIGN)
    assert "`ECZ` does not mean `continue` or local sweep" in _read(EN_DESIGN)


def test_topology_is_explicitly_outside_the_claim() -> None:
    ru_adr = _read(RU_ADR)
    en_adr = _read(EN_ADR)

    assert "Топология не является частью утверждения `PC-CATM`" in ru_adr
    assert "Topology is not part of the PC-CATM claim" in en_adr
    assert "Топологическое объяснение" in ru_adr
    assert "Topological explanation" in en_adr


def test_status_and_roadmap_point_to_runtime_freeze_next() -> None:
    ru_status = _read(ROOT / "STATUS.md")
    en_status = _read(ROOT / "STATUS_EN.md")
    ru_roadmap = _read(ROOT / "ROADMAP.md")
    en_roadmap = _read(ROOT / "ROADMAP_EN.md")

    for text in (ru_status, en_status, ru_roadmap, en_roadmap):
        assert "candidate-aware" in text
        assert "runtime" in text
        assert "authorization" in text

    assert "measurements запрещены" in ru_status
    assert "Measurements remain prohibited" in en_status
    assert "blocked_runtime_authorization" in ru_roadmap
    assert "blocked_runtime_authorization" in en_roadmap

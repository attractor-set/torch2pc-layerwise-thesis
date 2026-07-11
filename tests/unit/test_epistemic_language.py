from scripts.check_epistemic_language import scan_text


def test_unqualified_claim_is_detected() -> None:
    findings = scan_text("example.md", "Исследованием доказано превосходство метода.")
    assert findings


def test_methodological_negation_is_not_reported() -> None:
    findings = scan_text(
        "principles.md",
        "Не используются формулировки, в которых утверждается, что что-либо доказано.",
    )
    assert findings == []


def test_word_boundaries_do_not_match_unrelated_text() -> None:
    assert scan_text("example.md", "Подтверждено-подобная строка не является выводом.") == []

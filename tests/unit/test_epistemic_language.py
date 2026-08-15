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


def test_directly_negated_russian_guarantee_is_not_reported() -> None:
    findings = scan_text(
        "example.md",
        "Существование достаточного состояния не гарантирует экономической выгоды.",
    )
    assert findings == []


def test_unrelated_russian_negation_does_not_hide_guarantee() -> None:
    findings = scan_text(
        "example.md",
        "Метод не является эталоном, но гарантирует корректность результата.",
    )
    assert findings
    assert findings[0]["rule"] == "ru_guarantee"


def test_directly_negated_english_guarantee_is_not_reported() -> None:
    assert scan_text("example.md", "The result does not guarantee transfer.") == []


def test_unrelated_english_negation_does_not_hide_guarantee() -> None:
    findings = scan_text(
        "example.md",
        "The method is not a baseline, but guarantees correctness.",
    )
    assert findings
    assert findings[0]["rule"] == "en_guarantee"


def test_negated_english_guaranteed_adjective_is_not_reported() -> None:
    assert (
        scan_text(
            "example.md",
            "The horizon is not a guaranteed count of safe skips.",
        )
        == []
    )


def test_english_guaranteed_item_under_negated_implication_is_not_reported() -> None:
    assert (
        scan_text(
            "example.md",
            "One call does not imply one kernel, lower memory, or guaranteed acceleration.",
        )
        == []
    )

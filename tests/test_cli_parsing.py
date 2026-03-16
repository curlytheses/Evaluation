from run_exam_review import parse_csv_items, parse_factor_specialists


def test_parse_csv_items():
    assert parse_csv_items("a,b, c ,,") == ["a", "b", "c"]


def test_parse_factor_specialists():
    parsed = parse_factor_specialists("concept_accuracy=gemini:m,derivation=anthropic:c")
    assert parsed == {"concept_accuracy": "gemini:m", "derivation": "anthropic:c"}

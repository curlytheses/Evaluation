from src.rocketeval.io import iter_parsed_scripts


def test_iter_parsed_scripts_from_csv(tmp_path):
    input_file = tmp_path / "scripts.csv"
    input_file.write_text(
        "script_id,question_id,question_text,answer_text,max_marks,factors\n"
        "s1,q1,What?,Answer,10,concept_accuracy::6::Correctness||clarity::4::Clarity\n",
        encoding="utf-8",
    )

    scripts = list(iter_parsed_scripts(str(input_file)))

    assert len(scripts) == 1
    assert scripts[0].script_id == "s1"
    assert scripts[0].max_marks == 10
    assert [f.name for f in scripts[0].factors] == ["concept_accuracy", "clarity"]


def test_iter_parsed_scripts_requires_columns(tmp_path):
    input_file = tmp_path / "bad.csv"
    input_file.write_text("script_id,question_id\ns1,q1\n", encoding="utf-8")

    try:
        list(iter_parsed_scripts(str(input_file)))
        assert False, "Expected ValueError for missing required columns"
    except ValueError as exc:
        assert "Input CSV must include columns" in str(exc)

import csv
from pathlib import Path
from typing import Iterator

from .models import Factor, ParsedAnswerScript

_FACTOR_SEPARATOR = "||"
_FACTOR_PART_SEPARATOR = "::"


def _serialize_factors(factors: list[Factor]) -> str:
    return _FACTOR_SEPARATOR.join(
        f"{factor.name}{_FACTOR_PART_SEPARATOR}{factor.weight}{_FACTOR_PART_SEPARATOR}{factor.description}"
        for factor in factors
    )


def _parse_factors(raw: str) -> list[Factor]:
    factors: list[Factor] = []
    if not raw:
        return factors

    for item in raw.split(_FACTOR_SEPARATOR):
        if not item.strip():
            continue
        parts = item.split(_FACTOR_PART_SEPARATOR, 2)
        if len(parts) != 3:
            raise ValueError(
                "Invalid factors entry in CSV. Expected format 'name::weight::description'."
            )
        name, weight, description = (part.strip() for part in parts)
        factors.append(Factor(name=name, weight=float(weight), description=description))
    return factors


def iter_parsed_scripts(input_file: str) -> Iterator[ParsedAnswerScript]:
    with open(input_file, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        required = {
            "script_id",
            "question_id",
            "question_text",
            "answer_text",
            "max_marks",
            "factors",
        }
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError(
                "Input CSV must include columns: script_id, question_id, question_text, answer_text, max_marks, factors"
            )

        for row in reader:
            factors = _parse_factors(row.get("factors", ""))
            yield ParsedAnswerScript(
                script_id=(row.get("script_id") or "").strip(),
                question_id=(row.get("question_id") or "").strip(),
                question_text=row.get("question_text") or "",
                answer_text=row.get("answer_text") or "",
                max_marks=float(row.get("max_marks") or 0),
                factors=factors,
            )


def load_parsed_scripts(input_file: str) -> list[ParsedAnswerScript]:
    return list(iter_parsed_scripts(input_file))


def ensure_parent_dir(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def write_parsed_scripts_csv(path: str, scripts: list[ParsedAnswerScript]) -> None:
    ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "script_id",
                "question_id",
                "question_text",
                "answer_text",
                "max_marks",
                "factors",
            ],
        )
        writer.writeheader()
        for script in scripts:
            writer.writerow(
                {
                    "script_id": script.script_id,
                    "question_id": script.question_id,
                    "question_text": script.question_text,
                    "answer_text": script.answer_text,
                    "max_marks": script.max_marks,
                    "factors": _serialize_factors(script.factors),
                }
            )

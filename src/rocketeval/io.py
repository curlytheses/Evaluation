import json
from pathlib import Path

from .models import Factor, ParsedAnswerScript


def load_parsed_scripts(input_file: str) -> list[ParsedAnswerScript]:
    scripts: list[ParsedAnswerScript] = []
    with open(input_file, "r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            row = json.loads(line)
            factors = [Factor(**factor) for factor in row["factors"]]
            scripts.append(
                ParsedAnswerScript(
                    script_id=row["script_id"],
                    question_id=row["question_id"],
                    question_text=row["question_text"],
                    answer_text=row["answer_text"],
                    max_marks=float(row["max_marks"]),
                    factors=factors,
                )
            )
    return scripts

def ensure_parent_dir(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)

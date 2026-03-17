import csv
import json
import time
from typing import Any, Dict

from google import genai

API_KEY = ""
MODEL_NAME = "gemini-2.5-flash"
INPUT_FILE = "config/template/exam_parsed_script.sample.csv"
OUTPUT_FILE = "output.csv"

MAX_RETRIES = 3
RETRY_DELAY = 2

client = genai.Client(api_key=API_KEY)


def parse_factors(raw: str) -> list[dict[str, Any]]:
    factors: list[dict[str, Any]] = []
    for item in raw.split("||"):
        if not item.strip():
            continue
        name, weight, description = item.split("::", 2)
        factors.append({"name": name, "weight": float(weight), "description": description})
    return factors


def build_prompt(script: Dict[str, Any]) -> str:
    factor_template = {f["name"]: f"number (0–{f['weight']})" for f in script["factors"]}

    return f"""
ROLE
You are an exam answerscript evaluator.

TASK
Evaluate the student's answer using the provided rubric factors.

INPUT
Question:
{script['question_text']}

Student Answer:
{script['answer_text']}

Max Marks:
{script['max_marks']}

Rubric Factors:
{json.dumps(script['factors'], indent=2)}

STRICT INSTRUCTIONS
- Return ONLY valid JSON
- No markdown or extra text

OUTPUT FORMAT:
{json.dumps({'factor_scores': factor_template, 'total_score': 'number', 'justification': 'string'}, indent=2)}
"""


def build_schema(script: Dict[str, Any]) -> Dict[str, Any]:
    factor_props = {f["name"]: {"type": "number"} for f in script["factors"]}
    return {
        "type": "object",
        "properties": {
            "factor_scores": {
                "type": "object",
                "properties": factor_props,
                "required": list(factor_props.keys()),
            },
            "total_score": {"type": "number"},
            "justification": {"type": "string"},
        },
        "required": ["factor_scores", "total_score", "justification"],
    }


def validate_output(output: Dict[str, Any], script: Dict[str, Any]) -> bool:
    try:
        scores = output["factor_scores"]
        total = output["total_score"]

        for f in script["factors"]:
            name, weight = f["name"], f["weight"]
            if name not in scores or not (0 <= scores[name] <= weight):
                return False

        return 0 <= total <= script["max_marks"] and abs(sum(scores.values()) - total) <= 0.25
    except Exception:
        return False


def evaluate_script(script: Dict[str, Any]) -> Dict[str, Any]:
    prompt = build_prompt(script)
    schema = build_schema(script)

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={"temperature": 0.2, "response_mime_type": "application/json", "response_schema": schema},
            )
            parsed = json.loads(response.text.strip())
            if validate_output(parsed, script):
                return parsed
        except Exception as exc:
            print(f"[Retry {attempt + 1}] Error for {script['script_id']}: {exc}")

        time.sleep(RETRY_DELAY)

    return {"factor_scores": {}, "total_score": 0, "justification": "Evaluation failed after retries"}


def process_csv(input_path: str, output_path: str) -> None:
    with open(input_path, "r", encoding="utf-8", newline="") as infile, open(
        output_path, "w", encoding="utf-8", newline=""
    ) as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(
            outfile,
            fieldnames=["script_id", "question_id", "total_score", "factor_scores", "justification"],
        )
        writer.writeheader()

        for row in reader:
            script = {
                "script_id": row["script_id"],
                "question_id": row["question_id"],
                "question_text": row["question_text"],
                "answer_text": row["answer_text"],
                "max_marks": float(row["max_marks"]),
                "factors": parse_factors(row.get("factors", "")),
            }
            result = evaluate_script(script)
            writer.writerow(
                {
                    "script_id": script["script_id"],
                    "question_id": script["question_id"],
                    "total_score": result["total_score"],
                    "factor_scores": "; ".join(f"{k}:{v}" for k, v in result["factor_scores"].items()),
                    "justification": result["justification"],
                }
            )


if __name__ == "__main__":
    process_csv(INPUT_FILE, OUTPUT_FILE)

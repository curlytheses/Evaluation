import json
import time
from typing import Dict, Any, List
from google import genai

# =========================================
# CONFIG
# =========================================
API_KEY = ""
MODEL_NAME = "gemini-2.5-flash"
INPUT_FILE = "E:\\WorkLoad\\IITBHU\\Evaluation\\Evaluation\\config\\template\\exam_parsed_script.sample.jsonl"
OUTPUT_FILE = "output.jsonl"

MAX_RETRIES = 3
RETRY_DELAY = 2

client = genai.Client(api_key=API_KEY)

# =========================================
# PROMPT BUILDER
# =========================================
def build_prompt(script: Dict[str, Any]) -> str:
    factor_template = {
        f["name"]: f"number (0–{f['weight']})"
        for f in script["factors"]
    }

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
{json.dumps({
    "factor_scores": factor_template,
    "total_score": "number",
    "justification": "string"
}, indent=2)}

SCORING RULES
- Respect factor weights strictly
- Penalize incomplete reasoning
- Ensure sum consistency
"""

# =========================================
# DYNAMIC SCHEMA
# =========================================
def build_schema(script: Dict[str, Any]) -> Dict[str, Any]:
    factor_props = {
        f["name"]: {"type": "number"}
        for f in script["factors"]
    }

    return {
        "type": "object",
        "properties": {
            "factor_scores": {
                "type": "object",
                "properties": factor_props,
                "required": list(factor_props.keys())
            },
            "total_score": {"type": "number"},
            "justification": {"type": "string"}
        },
        "required": ["factor_scores", "total_score", "justification"]
    }

# =========================================
# VALIDATION
# =========================================
def validate_output(output: Dict[str, Any], script: Dict[str, Any]) -> bool:
    try:
        scores = output["factor_scores"]
        total = output["total_score"]

        for f in script["factors"]:
            name, weight = f["name"], f["weight"]

            if name not in scores:
                return False

            if not (0 <= scores[name] <= weight):
                return False

        if not (0 <= total <= script["max_marks"]):
            return False

        if abs(sum(scores.values()) - total) > 0.25:
            return False

        return True
    except Exception:
        return False

# =========================================
# GEMINI CALL
# =========================================
def evaluate_script(script: Dict[str, Any]) -> Dict[str, Any]:
    prompt = build_prompt(script)
    schema = build_schema(script)

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={
                    "temperature": 0.2,
                    "response_mime_type": "application/json",
                    "response_schema": schema
                }
            )

            raw = response.text.strip()
            parsed = json.loads(raw)

            if validate_output(parsed, script):
                return parsed

            print(f"[Retry {attempt+1}] Invalid output for {script['script_id']}")

        except Exception as e:
            print(f"[Retry {attempt+1}] Error for {script['script_id']}:", str(e))

        time.sleep(RETRY_DELAY)

    return {
        "factor_scores": {},
        "total_score": 0,
        "justification": "Evaluation failed after retries"
    }

# =========================================
# MAIN PIPELINE
# =========================================
def process_jsonl(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:

        for line in infile:
            script = json.loads(line.strip())

            print(f"Processing: {script['script_id']}")

            result = evaluate_script(script)

            # Merge input + output
            final_output = {
                "evaluation": result
            }

            outfile.write(json.dumps(final_output) + "\n")

    print("\n✅ All scripts processed successfully.")

# =========================================
# RUN
# =========================================
if __name__ == "__main__":
    process_jsonl(INPUT_FILE, OUTPUT_FILE)
import json
import logging
from typing import Literal
import openai
from rocketeval.engine import evaluate_script_with_debate
from rocketeval.io import ensure_parent_dir, load_parsed_scripts

logger = logging.getLogger("rich")

def run_exam_review_pipeline(
    input_file: str,
    output_file: str,
    reviewer_models: list[str],
    supreme_model: str,
    debate_rounds: int,
    pairing_strategy: Literal["all_to_all", "random", "round_robin"],
    random_seed: int,
    api_key: str | None = None,
    base_url: str | None = None,
) -> None:
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    scripts = load_parsed_scripts(input_file)
    ensure_parent_dir(output_file)

    with open(output_file, "w", encoding="utf-8") as file:
        for script in scripts:
            result = evaluate_script_with_debate(
                script=script,
                client=client,
                reviewer_models=reviewer_models,
                supreme_model=supreme_model,
                debate_rounds=debate_rounds,
                pairing_strategy=pairing_strategy,
                random_seed=random_seed,
            )
            file.write(json.dumps(result, ensure_ascii=False) + "\n")

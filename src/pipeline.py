import json
import logging

import openai

from rocketeval.config import ModelConfig, RuntimeConfig
from rocketeval.io import ensure_parent_dir, load_parsed_scripts
from rocketeval.orchestrator import EvaluationOrchestrator
from rocketeval.providers.openai_provider import OpenAIJsonProvider

logger = logging.getLogger("rich")


def run_exam_review_pipeline(
    input_file: str,
    output_file: str,
    reviewer_models: list[str],
    supreme_model: str,
    debate_rounds: int,
    pairing_strategy: str,
    random_seed: int,
    api_key: str | None = None,
    base_url: str | None = None,
) -> None:
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    provider = OpenAIJsonProvider(client=client)
    orchestrator = EvaluationOrchestrator(
        provider=provider,
        model_config=ModelConfig(reviewer_models=reviewer_models, supreme_model=supreme_model),
        runtime_config=RuntimeConfig(
            debate_rounds=debate_rounds,
            pairing_strategy=pairing_strategy,
            random_seed=random_seed,
        ),
    )

    scripts = load_parsed_scripts(input_file)
    ensure_parent_dir(output_file)
    with open(output_file, "w", encoding="utf-8") as file:
        for script in scripts:
            result = orchestrator.evaluate_script(script)
            file.write(json.dumps(result, ensure_ascii=False) + "\n")

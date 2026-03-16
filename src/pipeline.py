from __future__ import annotations
import json
import logging
import os
import anthropic
import openai
from google import genai
from src.rocketeval.config import ModelConfig, RuntimeConfig
from src.rocketeval.io import ensure_parent_dir, iter_parsed_scripts
from src.rocketeval.orchestrator import EvaluationOrchestrator
from src.rocketeval.providers.anthropic_provider import AnthropicProvider
from src.rocketeval.providers.gemini_provider import GeminiProvider
from src.rocketeval.providers.openai_provider import OpenAIProvider
from src.rocketeval.providers.router import MultiProviderRouter
logger = logging.getLogger("rich")

def load_env_file() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        return
    load_dotenv()

def build_router_from_env() -> MultiProviderRouter:
    load_env_file()

    # Read environment variables
    env = {
        "openai_key": os.getenv("OPENAI_API_KEY"),
        "openai_url": os.getenv("OPENAI_BASE_URL"),
        "anthropic_key": os.getenv("ANTHROPIC_API_KEY"),
        "gemini_key": os.getenv("GEMINI_API_KEY"),
    }

    if not env["openai_key"]:
        raise ValueError("OPENAI_API_KEY must be set in environment variables.")

    providers = {
        "openai": OpenAIProvider(
            client=openai.OpenAI(
                api_key=env["openai_key"],
                base_url=env["openai_url"]
            )
        )
    }

    optional_providers = {
        "anthropic": (
            env["anthropic_key"],
            lambda k: AnthropicProvider(
            client=anthropic.Anthropic(api_key=k)
        )
    ),
        "gemini": (
            env["gemini_key"],
            lambda k: GeminiProvider(
            client=genai.Client(api_key=k)
        )
    ),
}

    providers.update(
        {name: factory(key) for name, (key, factory) in optional_providers.items() if key}
    )

    return MultiProviderRouter(
        providers=providers,
        default_provider="openai"
    )

def review_pipeline(
    input_file: str,
    output_file: str,
    reviewer_models: list[str],
    supreme_model: str,
    factor_specialists: dict[str, str],
    debate_rounds: int,
    pairing_strategy: str,
    random_seed: int,
) -> None:
    router = build_router_from_env()
    orchestrator = EvaluationOrchestrator(
        provider=router,
        model_config=ModelConfig(
            reviewer_models=reviewer_models,
            supreme_model=supreme_model,
            factor_specialists=factor_specialists,
        ),
        runtime_config=RuntimeConfig(
            debate_rounds=debate_rounds,
            pairing_strategy=pairing_strategy,
            random_seed=random_seed,
        ),
    )

    ensure_parent_dir(output_file)
    with open(output_file, "w", encoding="utf-8") as file:
        for script in iter_parsed_scripts(input_file):
            result = orchestrator.evaluate_script(script)
            file.write(json.dumps(result, ensure_ascii=False) + "\n")

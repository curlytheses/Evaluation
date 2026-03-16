"""Batch pipeline for evaluating parsed answer scripts."""

from __future__ import annotations

import json
import logging

import openai

from rocketeval.config import ModelConfig, RuntimeConfig
from rocketeval.io import ensure_parent_dir, load_parsed_scripts
from rocketeval.orchestrator import EvaluationOrchestrator
from rocketeval.providers.anthropic_provider import AnthropicJsonProvider
from rocketeval.providers.gemini_provider import GeminiJsonProvider
from rocketeval.providers.openai_provider import OpenAIJsonProvider
from rocketeval.providers.router import MultiProviderRouter

logger = logging.getLogger("rich")


def build_router(
    openai_api_key: str | None,
    openai_base_url: str | None,
    anthropic_api_key: str | None,
    gemini_api_key: str | None,
) -> MultiProviderRouter:
    """Create router with configured providers; OpenAI-compatible provider is always present."""
    providers = {
        "openai": OpenAIJsonProvider(client=openai.OpenAI(api_key=openai_api_key, base_url=openai_base_url))
    }

    if anthropic_api_key:
        providers["anthropic"] = AnthropicJsonProvider(api_key=anthropic_api_key)
    if gemini_api_key:
        providers["gemini"] = GeminiJsonProvider(api_key=gemini_api_key)

    return MultiProviderRouter(providers=providers, default_provider="openai")


def run_exam_review_pipeline(
    input_file: str,
    output_file: str,
    reviewer_models: list[str],
    supreme_model: str,
    factor_specialists: dict[str, str],
    debate_rounds: int,
    pairing_strategy: str,
    random_seed: int,
    openai_api_key: str | None = None,
    openai_base_url: str | None = None,
    anthropic_api_key: str | None = None,
    gemini_api_key: str | None = None,
) -> None:
    """Evaluate all scripts in input JSONL and write result JSONL."""
    router = build_router(openai_api_key, openai_base_url, anthropic_api_key, gemini_api_key)
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

    scripts = load_parsed_scripts(input_file)
    ensure_parent_dir(output_file)

    with open(output_file, "w", encoding="utf-8") as file:
        for script in scripts:
            result = orchestrator.evaluate_script(script)
            file.write(json.dumps(result, ensure_ascii=False) + "\n")

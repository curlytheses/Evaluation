from typing import Any, Literal
import openai
from .config import ModelConfig, RuntimeConfig
from .models import ParsedAnswerScript
from .orchestrator import EvaluationOrchestrator
from .providers.openai_provider import OpenAIProvider
from .providers.router import MultiProviderRouter

def evaluate_script_with_debate(
    script: ParsedAnswerScript, client: openai.OpenAI,
    reviewer_models: list[str], supreme_model: str,
    debate_rounds: int = 4, pairing_strategy: Literal["all_to_all", "random", "round_robin"] = "all_to_all",
    random_seed: int = 42, factor_specialists: dict[str, str] | None = None,
) -> dict[str, Any]:
    router = MultiProviderRouter(providers={"openai": OpenAIProvider(client=client)}, default_provider="openai")
    orchestrator = EvaluationOrchestrator(
        provider=router,
        model_config=ModelConfig(
            reviewer_models=reviewer_models,
            supreme_model=supreme_model,
            factor_specialists=factor_specialists or {},
        ),
        runtime_config=RuntimeConfig(
            debate_rounds=debate_rounds,
            pairing_strategy=pairing_strategy,
            random_seed=random_seed,
        ),
    )
    return orchestrator.evaluate_script(script)

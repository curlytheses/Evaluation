from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
PairingStrategy = Literal["all_to_all", "random", "round_robin"]

@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    debate_rounds: int = 6
    pairing_strategy: PairingStrategy = "all_to_all"
    random_seed: int = 42

    def validate(self) -> None:
        if self.debate_rounds < 1:
            raise ValueError("debate_rounds must be >= 1")

@dataclass(frozen=True, slots=True)
class ModelConfig:
    reviewer_models: list[str] = field(default_factory=list)
    supreme_model: str = "openai:gpt-4o"
    factor_specialists: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if len(self.reviewer_models) < 2:
            raise ValueError("At least two reviewer models are required for debate.")
        if not self.supreme_model:
            raise ValueError("supreme_model is required.")
        if any(not model for model in self.reviewer_models):
            raise ValueError("reviewer_models cannot include empty model names.")

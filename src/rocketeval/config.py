from dataclasses import dataclass, field
from typing import Literal

PairingStrategy = Literal["all_to_all", "random", "round_robin"]


@dataclass(frozen=True)
class RuntimeConfig:
    debate_rounds: int = 6
    pairing_strategy: PairingStrategy = "all_to_all"
    random_seed: int = 42


@dataclass(frozen=True)
class ModelConfig:
    reviewer_models: list[str] = field(default_factory=list)
    supreme_model: str = "gpt-4o"

    def validate(self) -> None:
        if len(self.reviewer_models) < 2:
            raise ValueError("At least two reviewer models are required for debate.")
        if not self.supreme_model:
            raise ValueError("supreme_model is required.")

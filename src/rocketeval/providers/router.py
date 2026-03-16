"""Provider router for model IDs in provider:model format."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class JsonProvider(Protocol):
    def complete_json(self, model: str, prompt: str) -> dict:
        """Execute a completion and return parsed JSON."""


@dataclass(slots=True)
class MultiProviderRouter:
    providers: dict[str, JsonProvider]
    default_provider: str = "openai"

    def complete_json(self, agent_model: str, prompt: str) -> dict:
        provider_name, model = self._split_agent_model(agent_model)
        provider = self.providers.get(provider_name)
        if provider is None:
            raise ValueError(
                f"Provider '{provider_name}' not configured. Available providers: {sorted(self.providers.keys())}"
            )
        return provider.complete_json(model=model, prompt=prompt)

    def _split_agent_model(self, agent_model: str) -> tuple[str, str]:
        if ":" in agent_model:
            provider_name, model = agent_model.split(":", 1)
        else:
            provider_name, model = self.default_provider, agent_model

        provider_name = provider_name.strip()
        model = model.strip()
        if not provider_name or not model:
            raise ValueError(f"Invalid agent model identifier: {agent_model!r}")
        return provider_name, model

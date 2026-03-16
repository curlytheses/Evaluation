from dataclasses import dataclass
from typing import Protocol


class JsonProvider(Protocol):
    def complete_json(self, model: str, prompt: str) -> dict:
        ...


@dataclass
class MultiProviderRouter:
    providers: dict[str, JsonProvider]
    default_provider: str = "openai"

    def complete_json(self, agent_model: str, prompt: str) -> dict:
        if ":" in agent_model:
            provider_name, model = agent_model.split(":", 1)
        else:
            provider_name, model = self.default_provider, agent_model
        provider = self.providers.get(provider_name)
        if provider is None:
            raise ValueError(
                f"Provider '{provider_name}' not configured. Available providers: {sorted(self.providers.keys())}"
            )
        return provider.complete_json(model=model, prompt=prompt)

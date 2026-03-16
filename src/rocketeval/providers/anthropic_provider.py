from __future__ import annotations
import json
from dataclasses import field
from typing import Any

class AnthropicJsonProvider:
    api_key: str
    max_tokens: int = 1500
    temperature: float = 0.0
    _client: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            import anthropic  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "Anthropic SDK is required. Install with `pip install anthropic`."
            ) from exc
        self._client = anthropic.Anthropic(api_key=self.api_key)

    def complete_json(self, model: str, prompt: str) -> dict:
        response = self._client.messages.create(
            model=model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        text_parts = [part.text for part in response.content if getattr(part, "type", "") == "text"]
        return json.loads("".join(text_parts) or "{}")

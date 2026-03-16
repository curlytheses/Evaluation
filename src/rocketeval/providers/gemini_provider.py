"""Gemini provider using official Google Generative AI Python SDK."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class GeminiJsonProvider:
    api_key: str
    temperature: float = 0.0
    _client: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "Google Generative AI SDK is required. Install with `pip install google-generativeai`."
            ) from exc

        genai.configure(api_key=self.api_key)
        self._client = genai

    def complete_json(self, model: str, prompt: str) -> dict:
        response = self._client.GenerativeModel(model).generate_content(
            prompt,
            generation_config={
                "temperature": self.temperature,
                "response_mime_type": "application/json",
            },
        )
        text = getattr(response, "text", "") or "{}"
        return json.loads(text)

import json
import urllib.request
from dataclasses import dataclass


@dataclass
class AnthropicJsonProvider:
    api_key: str
    max_tokens: int = 1500
    temperature: float = 0.0

    def complete_json(self, model: str, prompt: str) -> dict:
        payload = json.dumps(
            {
                "model": model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            method="POST",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        with urllib.request.urlopen(req) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        text_parts = [part.get("text", "") for part in raw.get("content", []) if part.get("type") == "text"]
        return json.loads("".join(text_parts) or "{}")

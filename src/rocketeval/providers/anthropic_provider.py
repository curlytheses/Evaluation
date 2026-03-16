from dataclasses import dataclass
import json
import anthropic

@dataclass(slots=True)
class AnthropicProvider:
    client: anthropic.Anthropic
    temperature: float = 0.0
    max_tokens: int = 1500

    def complete_json(self, model: str, prompt: str) -> dict:
        response = self.client.messages.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        text = "".join(
            part.text for part in response.content if part.type == "text"
        ).strip()

        if not text:
            return {}

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise ValueError(f"Model returned invalid JSON:\n{text}")
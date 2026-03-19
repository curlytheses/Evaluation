from dataclasses import dataclass
import json
from mistralai.client import Mistral

@dataclass(slots=True)
class MistralProvider:
    client: Mistral
    temperature: float = 0.0
    max_tokens: int = 1500

    def complete_json(self, model: str, prompt: str, response_schema: dict | None = None) -> dict:
        _ = response_schema
        response = self.client.chat.complete(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content or "{}"
        print(f"Mistral raw response:\n{text}")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise ValueError(f"Model returned invalid JSON:\n{text}")
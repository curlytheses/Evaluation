from dataclasses import dataclass
import json
import cohere

@dataclass(slots=True)
class CohereProvider:
    client: cohere.ClientV2
    temperature: float = 0.0
    max_tokens: int = 1500

    def complete_json(self, model: str, prompt: str, response_schema: dict | None = None) -> dict:
        _ = response_schema
        response = self.client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
        )
        text = response.message.content[0].text or "{}"
        print(f"Cohere raw response:\n{text}")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise ValueError(f"Model returned invalid JSON:\n{text}")
from dataclasses import dataclass
import json
from google import genai

@dataclass(slots=True)
class GeminiProvider:
    client: genai.Client
    temperature: float = 0.0
    max_tokens: int = 1500

    def complete_json(self, model: str, prompt: str) -> dict:
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "response_mime_type": "application/json",
            },
        )

        text = getattr(response, "text", "").strip()

        if not text:
            return {}

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise ValueError(f"Model returned invalid JSON:\n{text}")
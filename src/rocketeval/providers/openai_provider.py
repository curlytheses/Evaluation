from dataclasses import dataclass
import openai
from ..llm import chat_json
@dataclass(slots=True)
class OpenAIProvider:
    client: openai.OpenAI
    temperature: float = 0.0
    max_tokens: int = 1500

    def complete_json(self, model: str, prompt: str) -> dict:
        return chat_json(
            client=self.client,
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

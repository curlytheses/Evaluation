import json
from typing import Any

import openai

class JsonResponseError(RuntimeError):
    pass

def chat_json(
    client: openai.OpenAI,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 1500,
    retries: int = 3,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for _ in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                messages=messages,
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception as exc:
            last_error = exc
    raise JsonResponseError(f"Failed to receive valid JSON response: {last_error}")

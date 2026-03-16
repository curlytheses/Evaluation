from typing import Protocol


class JsonLLM(Protocol):
    def complete_json(self, model: str, prompt: str) -> dict:
        ...

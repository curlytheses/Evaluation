from dataclasses import dataclass


@dataclass
class MockJsonProvider:
    """Deterministic provider for tests and dry-runs."""

    responses: list[dict]

    def __post_init__(self) -> None:
        self._idx = 0

    def complete_json(self, model: str, prompt: str) -> dict:
        if self._idx >= len(self.responses):
            raise RuntimeError("No more mock responses configured")
        response = self.responses[self._idx]
        self._idx += 1
        return response

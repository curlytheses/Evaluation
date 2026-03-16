from dataclasses import dataclass, field


@dataclass
class MockJsonProvider:
    """Deterministic provider for tests and dry-runs."""

    responses: list[dict] | None = None
    responses_by_model: dict[str, list[dict]] | None = None
    calls: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._idx = 0

    def complete_json(self, model: str, prompt: str) -> dict:
        self.calls.append(model)
        if self.responses_by_model is not None:
            queue = self.responses_by_model.get(model, [])
            if not queue:
                raise RuntimeError(f"No more mock responses configured for model={model}")
            return queue.pop(0)

        if self.responses is None or self._idx >= len(self.responses):
            raise RuntimeError("No more mock responses configured")
        response = self.responses[self._idx]
        self._idx += 1
        return response

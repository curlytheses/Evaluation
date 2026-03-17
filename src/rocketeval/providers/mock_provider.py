from dataclasses import dataclass, field


@dataclass
class MockJsonProvider:
    responses: list[dict | Exception] | None = None
    responses_by_model: dict[str, list[dict | Exception]] | None = None
    calls: list[str] = field(default_factory=list)
    _idx: int = field(init=False, default=0, repr=False)

    def complete_json(self, model: str, prompt: str, response_schema: dict | None = None) -> dict:
        _ = prompt, response_schema
        self.calls.append(model)
        if self.responses_by_model is not None:
            queue = self.responses_by_model.get(model, [])
            if not queue:
                raise RuntimeError(f"No more mock responses configured for model={model}")
            response = queue.pop(0)
            if isinstance(response, Exception):
                raise response
            return response

        if self.responses is None or self._idx >= len(self.responses):
            raise RuntimeError("No more mock responses configured")
        response = self.responses[self._idx]
        self._idx += 1
        if isinstance(response, Exception):
            raise response
        return response

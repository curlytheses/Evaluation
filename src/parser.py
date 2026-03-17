import argparse

def parse_csv_items(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]

def parse_factor_specialists(raw: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in parse_csv_items(raw):
        if "=" not in item:
            raise ValueError(
                f"Invalid --factor_specialists item {item!r}. Expected format: factor=provider:model"
            )
        factor, model = item.split("=", 1)
        factor = factor.strip()
        model = model.strip()
        if not factor or not model:
            raise ValueError(
                f"Invalid --factor_specialists item {item!r}. Expected non-empty factor and model"
            )
        mapping[factor] = model
    return mapping

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Answer script evaluation with multi-LLM debate, "
            "Factor specialists, and Meta reviewer."
        )
    )
    parser.add_argument("--input_file", required=True, help="CSV with parsed answer scripts")
    parser.add_argument("--output_file", required=True, help="Output CSV file")
    parser.add_argument(
        "--reviewer_models",
        required=True,
        help=(
            "Comma-separated reviewer agent models, e.g. "
            "gemini:gemini-1.5-pro,anthropic:claude-3-5-sonnet,openai:gpt-5.3"
        ),
    )
    parser.add_argument(
        "--supreme_model",
        required=True,
        help="Supreme model in provider:model format, typically openai:gpt-4o",
    )
    parser.add_argument(
        "--factor_specialists",
        default="",
        help=(
            "Comma-separated factor=model mapping, e.g. "
            "concept_accuracy=gemini:gemini-1.5-pro,"
            "derivation=anthropic:claude-3-5-sonnet,"
            "clarity=openai:gpt-5.3"
        ),
    )
    parser.add_argument("--debate_rounds", type=int, default=6, help="Maximum debate rounds")
    parser.add_argument(
        "--pairing_strategy",
        choices=["all_to_all", "random", "round_robin"],
        default="all_to_all",
        help="Reviewer pairing strategy for each debate round",
    )
    parser.add_argument("--random_seed", type=int, default=42, help="Random seed for random pairing")
    return parser
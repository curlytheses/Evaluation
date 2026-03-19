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
    parser.add_argument("--input_file", required=True)
    parser.add_argument("--output_file", required=True)
    parser.add_argument(
        "--reviewer_models",
        required=True
    )
    parser.add_argument(
        "--supreme_model",
        required=True
    )
    parser.add_argument(
        "--factor_specialists",
        default=""
    )
    parser.add_argument("--debate_rounds", type=int, default=6, help="Maximum debate rounds")
    parser.add_argument(
        "--pairing_strategy",
        choices=["all_to_all", "random", "round_robin"],
        default="all_to_all"
    )
    parser.add_argument("--random_seed", type=int, default=42)
    return parser
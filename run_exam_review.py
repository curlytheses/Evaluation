"""CLI entrypoint for multi-LLM IIT-style answer evaluation."""

from __future__ import annotations

import argparse
import logging



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
            "IIT-style answer script evaluation with multi-LLM debate, "
            "factor specialists, and OpenAI supreme reviewer."
        )
    )
    parser.add_argument("--input_file", required=True, help="JSONL with parsed answer scripts")
    parser.add_argument("--output_file", required=True, help="Output JSONL file")
    parser.add_argument(
        "--reviewer_models",
        required=True,
        help=(
            "Comma-separated reviewer agent models, e.g. "
            "gemini:gemini-1.5-pro,anthropic:claude-3-5-sonnet,openai:qwen-max"
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
            "clarity=openai:qwen-max"
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

    parser.add_argument("--openai_api_key", default=None)
    parser.add_argument("--openai_base_url", default=None)
    parser.add_argument("--anthropic_api_key", default=None)
    parser.add_argument("--gemini_api_key", default=None)
    return parser


def main() -> None:
    from rich.logging import RichHandler

    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    parser = build_parser()
    args = parser.parse_args()

    reviewer_models = parse_csv_items(args.reviewer_models)
    factor_specialists = parse_factor_specialists(args.factor_specialists)

    from pipeline import run_exam_review_pipeline

    run_exam_review_pipeline(
        input_file=args.input_file,
        output_file=args.output_file,
        reviewer_models=reviewer_models,
        supreme_model=args.supreme_model,
        factor_specialists=factor_specialists,
        debate_rounds=args.debate_rounds,
        pairing_strategy=args.pairing_strategy,
        random_seed=args.random_seed,
        openai_api_key=args.openai_api_key,
        openai_base_url=args.openai_base_url,
        anthropic_api_key=args.anthropic_api_key,
        gemini_api_key=args.gemini_api_key,
    )


if __name__ == "__main__":
    main()

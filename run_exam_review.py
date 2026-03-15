import argparse
import logging
from rich.logging import RichHandler

from pipeline import run_exam_review_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()]
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="IIT-style answer script evaluation with multi-LLM debate and supreme reviewer."
    )
    parser.add_argument("--input_file", required=True, help="JSONL with parsed answer scripts")
    parser.add_argument("--output_file", required=True, help="Output JSONL file")
    parser.add_argument(
        "--reviewer_models",
        required=True,
        help="Comma-separated reviewer model names (at least two)",
    )
    parser.add_argument("--supreme_model", required=True, help="Model name for the supreme reviewer")
    parser.add_argument("--debate_rounds", type=int, default=6, help="Maximum debate rounds")
    parser.add_argument(
        "--pairing_strategy",
        choices=["all_to_all", "random", "round_robin"],
        default="all_to_all",
        help="Reviewer pairing strategy for each debate round",
    )
    parser.add_argument("--random_seed", type=int, default=42, help="Random seed for random pairing")
    parser.add_argument("--api_key", default=None, help="Optional API key override")
    parser.add_argument("--base_url", default=None, help="Optional OpenAI-compatible base URL")

    args = parser.parse_args()
    reviewer_models = [m.strip() for m in args.reviewer_models.split(",") if m.strip()]

    run_exam_review_pipeline(
        input_file=args.input_file,
        output_file=args.output_file,
        reviewer_models=reviewer_models,
        supreme_model=args.supreme_model,
        debate_rounds=args.debate_rounds,
        pairing_strategy=args.pairing_strategy,
        random_seed=args.random_seed,
        api_key=args.api_key,
        base_url=args.base_url,
    )

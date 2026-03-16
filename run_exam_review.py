from __future__ import annotations
import logging
from Evaluation.src.parser import build_parser, parse_csv_items, parse_factor_specialists
from src.pipeline import review_pipeline
from rich.logging import RichHandler

def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    parser = build_parser()
    args = parser.parse_args(argv)

    reviewer_models = parse_csv_items(args.reviewer_models)
    factor_specialists = parse_factor_specialists(args.factor_specialists)

    review_pipeline(
        input_file=args.input_file,
        output_file=args.output_file,
        reviewer_models=reviewer_models,
        supreme_model=args.supreme_model,
        factor_specialists=factor_specialists,
        debate_rounds=args.debate_rounds,
        pairing_strategy=args.pairing_strategy,
        random_seed=args.random_seed,
    )

if __name__ == "__main__":
    main()


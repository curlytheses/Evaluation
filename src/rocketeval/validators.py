from typing import Any

from .models import Factor


def clip_factor_scores(factors: list[Factor], scores: dict[str, Any]) -> dict[str, float]:
    factor_weights = {factor.name: factor.weight for factor in factors}
    clipped: dict[str, float] = {}
    for factor_name, factor_weight in factor_weights.items():
        value = float(scores.get(factor_name, 0.0))
        clipped[factor_name] = round(min(max(value, 0.0), float(factor_weight)), 2)
    return clipped


def normalize_total_score(max_marks: float, proposed_score: Any, fallback: float) -> float:
    return round(min(max(float(proposed_score), 0.0), max_marks), 2) if proposed_score is not None else round(
        min(max(float(fallback), 0.0), max_marks),
        2,
    )

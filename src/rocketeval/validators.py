from __future__ import annotations
from typing import Any
from .models import Factor, ParsedAnswerScript

DEFAULT_ROUND_DIGITS = 2

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)

def clip_factor_scores(factors: list[Factor], scores: dict[str, Any]) -> dict[str, float]:
    factor_weights = {factor.name: factor.weight for factor in factors}
    clipped: dict[str, float] = {}
    for factor_name, factor_weight in factor_weights.items():
        value = safe_float(scores.get(factor_name, 0.0), default=0.0)
        clipped[factor_name] = round(min(max(value, 0.0), float(factor_weight)), DEFAULT_ROUND_DIGITS)
    return clipped

def normalize_total_score(max_marks: float, proposed_score: Any, fallback: float) -> float:
    candidate = safe_float(proposed_score, default=fallback)
    normalized = min(max(candidate, 0.0), max_marks)
    return round(normalized, DEFAULT_ROUND_DIGITS)


def validate_review_output(output: dict[str, Any], script: ParsedAnswerScript) -> bool:
    try:
        scores = output["factor_scores"]
        total = safe_float(output["total_score"])

        for factor in script.factors:
            if factor.name not in scores:
                return False
            score = safe_float(scores[factor.name], default=-1)
            if not (0 <= score <= factor.weight):
                return False

        if not (0 <= total <= script.max_marks):
            return False

        if abs(sum(safe_float(value) for value in scores.values()) - total) > 0.25:
            return False

        return isinstance(output.get("justification"), str)
    except Exception:
        return False

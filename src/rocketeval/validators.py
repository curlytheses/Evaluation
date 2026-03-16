"""Validation and normalization helpers for rubric scoring."""

from __future__ import annotations

from typing import Any

from .models import Factor


DEFAULT_ROUND_DIGITS = 2


def safe_float(value: Any, default: float = 0.0) -> float:
    """Best-effort conversion to float with a deterministic fallback."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def clip_factor_scores(factors: list[Factor], scores: dict[str, Any]) -> dict[str, float]:
    """Clip factor scores into each factor's valid [0, weight] range."""
    factor_weights = {factor.name: factor.weight for factor in factors}
    clipped: dict[str, float] = {}
    for factor_name, factor_weight in factor_weights.items():
        value = safe_float(scores.get(factor_name, 0.0), default=0.0)
        clipped[factor_name] = round(min(max(value, 0.0), float(factor_weight)), DEFAULT_ROUND_DIGITS)
    return clipped


def normalize_total_score(max_marks: float, proposed_score: Any, fallback: float) -> float:
    """Normalize total score to [0, max_marks] using fallback if missing/invalid."""
    candidate = safe_float(proposed_score, default=fallback)
    normalized = min(max(candidate, 0.0), max_marks)
    return round(normalized, DEFAULT_ROUND_DIGITS)

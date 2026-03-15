import random
from typing import Any, Literal
from .models import DebateTurn, Factor

def clip_scores(factors: list[Factor], scores: dict[str, Any]) -> dict[str, float]:
    factor_weights = {factor.name: factor.weight for factor in factors}
    clipped: dict[str, float] = {}
    for factor_name, factor_weight in factor_weights.items():
        value = float(scores.get(factor_name, 0.0))
        clipped[factor_name] = round(min(max(value, 0.0), float(factor_weight)), 2)
    return clipped

def all_supporting(turns: list[DebateTurn], reviewer_ids: list[str]) -> bool:
    if len(turns) < 2 * len(reviewer_ids):
        return False

    last_two_round_ids = sorted({turn.round_id for turn in turns})[-2:]
    latest_turns = [turn for turn in turns if turn.round_id in last_two_round_ids]

    for turn in latest_turns:
        if not turn.stance_by_reviewer:
            return False
        if any(stance != "support" for stance in turn.stance_by_reviewer.values()):
            return False
    return True

def select_peer_set(
    reviewer_ids: list[str],
    reviewer_id: str,
    strategy: Literal["all_to_all", "random", "round_robin"],
    rng: random.Random,
) -> list[str]:
    peers = [candidate for candidate in reviewer_ids if candidate != reviewer_id]
    if strategy == "all_to_all" or len(peers) <= 1:
        return peers
    if strategy == "random":
        return [rng.choice(peers)]

    index = reviewer_ids.index(reviewer_id)
    return [reviewer_ids[(index + 1) % len(reviewer_ids)]]

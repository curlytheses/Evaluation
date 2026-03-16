import random
from typing import Any, Literal
from .debate import all_supporting_last_two_rounds, select_peer_set as debate_select_peer_set
from .models import DebateTurn, Factor
from .validators import clip_factor_scores

def clip_scores(factors: list[Factor], scores: dict[str, Any]) -> dict[str, float]:
    return clip_factor_scores(factors, scores)

def all_supporting(turns: list[DebateTurn], reviewer_ids: list[str]) -> bool:
    return all_supporting_last_two_rounds(turns, reviewer_ids)

def select_peer_set(
    reviewer_ids: list[str],
    reviewer_id: str,
    strategy: Literal["all_to_all", "random", "round_robin"],
    rng: random.Random,
) -> list[str]:
    return debate_select_peer_set(reviewer_ids, reviewer_id, strategy, rng)

__all__ = ["clip_scores", "all_supporting", "select_peer_set"]

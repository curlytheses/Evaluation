import random
from typing import Literal
from .models import DebateTurn

PairingStrategy = Literal["all_to_all", "random", "round_robin"]


def select_peer_set(
    reviewer_ids: list[str],
    reviewer_id: str,
    strategy: PairingStrategy,
    rng: random.Random,
) -> list[str]:
    peers = [candidate for candidate in reviewer_ids if candidate != reviewer_id]
    if strategy == "all_to_all" or len(peers) <= 1:
        return peers
    if strategy == "random":
        return [rng.choice(peers)]

    index = reviewer_ids.index(reviewer_id)
    return [reviewer_ids[(index + 1) % len(reviewer_ids)]]


def all_supporting_last_two_rounds(turns: list[DebateTurn], reviewer_ids: list[str]) -> bool:
    if len(turns) < 2 * len(reviewer_ids):
        return False
    last_two_round_ids = sorted({turn.round_id for turn in turns})[-2:]
    latest_turns = [turn for turn in turns if turn.round_id in last_two_round_ids]
    if len(latest_turns) < 2 * len(reviewer_ids):
        return False
    for turn in latest_turns:
        if not turn.stance_by_reviewer:
            return False
        if any(stance != "support" for stance in turn.stance_by_reviewer.values()):
            return False
    return True

from collections.abc import Sequence
from dataclasses import dataclass

from ..result import GameResult


@dataclass(frozen=True, slots=True)
class Outcome:
    """A decided or drawn contest between two competitors, scored for the first."""

    first: str
    second: str
    score: float


def contests(results: Sequence[GameResult], unit: str) -> list[Outcome]:
    """Two-competitor outcomes per duel, or per match when unit is "match"."""
    if unit not in ("game", "match"):
        raise ValueError('unit must be "game" or "match"')
    outcomes, seen = [], set()
    for result in results:
        if len(result.seats) != 2:
            continue
        first, second = sorted(result.competitors)
        if unit == "game":
            winner = result.winner
        else:
            if result.kind != "match" or result.index in seen:
                continue
            seen.add(result.index)
            winner = result.match_winner
        outcomes.append(Outcome(first, second, 0.5 if winner is None else float(winner == first)))
    return outcomes

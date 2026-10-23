from dataclasses import dataclass
from enum import StrEnum

from ..deck import Deck
from ..episode import EpisodeResult
from .rules import MatchRules


class MatchPhase(StrEnum):
    FIRST_PLAYER = "first_player"
    DUEL = "duel"
    SIDE_DECKING = "side_decking"
    FINISHED = "finished"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class DuelResult:
    index: int
    seed: int
    seat_players: tuple[int, int]
    winner: int | None
    reason: str
    episode: EpisodeResult | None = None
    match_kill: int | None = None


@dataclass(frozen=True, slots=True)
class MatchResult:
    winner: int | None
    scores: tuple[int, int]
    draws: int
    duels: tuple[DuelResult, ...]
    terminated: bool
    truncated: bool
    reason: str

    @property
    def returns(self) -> tuple[float, float]:
        if self.winner is None:
            return 0.0, 0.0
        return (1.0, -1.0) if self.winner == 0 else (-1.0, 1.0)


@dataclass(frozen=True, slots=True)
class SideDeckInput:
    """Own deck and public series history; no opponent deck or submission."""

    player: int
    deck: Deck
    scores: tuple[int, int]
    duels: tuple[DuelResult, ...]
    rules: MatchRules


@dataclass(frozen=True, slots=True)
class FirstPlayerInput:
    player: int
    scores: tuple[int, int]
    duels: tuple[DuelResult, ...]


@dataclass(frozen=True, slots=True)
class MatchStart:
    player: int
    deck: Deck
    rules: MatchRules
    seed: int

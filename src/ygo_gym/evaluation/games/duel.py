from dataclasses import asdict, dataclass

from ...episode import play
from ...rules import DuelConfig
from ..competitor import Competitor
from ..result import GameResult
from .seats import seated, winner_name


@dataclass(frozen=True, slots=True)
class DuelGame:
    """A single duel; the first competitor takes engine seat 0, which plays first."""

    players: tuple[Competitor, Competitor]
    seed: int
    config: DuelConfig | None = None
    max_steps: int | None = None
    kind = "duel"

    def __post_init__(self):
        object.__setattr__(self, "players", tuple(self.players))
        if len(self.players) != 2 or any(p.deck is None for p in self.players):
            raise ValueError("duels need two competitors with decks")
        if self.players[0].name == self.players[1].name:
            raise ValueError("duel competitors need distinct names")

    @property
    def competitors(self) -> tuple[Competitor, ...]:
        return self.players

    def play(self, engine, index: int) -> list[GameResult]:
        first, second = self.players
        with seated(self.players) as seats:
            with engine.create_duel(first.deck, second.deck, seed=self.seed, config=self.config) as duel:
                result = play(duel, agents=seats, max_steps=self.max_steps, seed=self.seed)
                replay = duel.replay()
        winner = None if result.outcome is None else winner_name(seats, result.outcome.winner)
        return [
            GameResult(
                index, 0, self.kind, None, self.seed, tuple(seat.results[0] for seat in seats), winner,
                None, result.reason, None, result.returns, result.step_count, result.terminated,
                result.truncated, replay,
            )
        ]

    def describe(self) -> dict:
        return {"kind": self.kind, "competitors": [p.name for p in self.players], "seed": self.seed,
                "config": None if self.config is None else asdict(self.config), "max_steps": self.max_steps}

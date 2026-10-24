from dataclasses import dataclass, field

from ...match import Match, MatchRules, play_match
from ..competitor import Competitor
from ..result import GameResult
from .seats import seated


@dataclass(frozen=True, slots=True)
class MatchGame:
    """A best-of-N series with side decking, reported as one result per duel."""

    players: tuple[Competitor, Competitor]
    seed: int
    rules: MatchRules = field(default_factory=MatchRules)
    kind = "match"

    def __post_init__(self):
        object.__setattr__(self, "players", tuple(self.players))
        if len(self.players) != 2 or any(p.deck is None for p in self.players):
            raise ValueError("matches need two competitors with decks")
        if self.players[0].name == self.players[1].name:
            raise ValueError("match competitors need distinct names")

    @property
    def competitors(self) -> tuple[Competitor, ...]:
        return self.players

    def play(self, engine, index: int) -> list[GameResult]:
        decks = tuple(p.deck for p in self.players)
        with seated(self.players) as seats, Match(engine, decks, rules=self.rules, seed=self.seed) as match:
            result = play_match(match, agents=seats, seed=self.seed)
        names = [p.name for p in self.players]
        match_winner = None if result.winner is None else names[result.winner]
        rows = []
        for duel in result.duels:
            order = duel.seat_players
            episode = duel.episode
            rows.append(
                GameResult(
                    index, duel.index, self.kind, None, duel.seed,
                    tuple(seats[player].results[duel.index] for player in order),
                    None if duel.winner is None else names[duel.winner], match_winner, duel.reason, None,
                    (0.0, 0.0) if episode is None else episode.returns,
                    0 if episode is None else episode.step_count,
                    episode is not None and episode.terminated, episode is not None and episode.truncated,
                    duel.replay,
                )
            )
        return rows

    def describe(self) -> dict:
        return {"kind": self.kind, "competitors": [p.name for p in self.players], "seed": self.seed,
                "rules": self.rules}

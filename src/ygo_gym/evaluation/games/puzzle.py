from dataclasses import dataclass

from ...episode import play
from ...puzzle import Puzzle
from ..competitor import Competitor
from ..result import GameResult
from .seats import seated


@dataclass(frozen=True, slots=True)
class PuzzleGame:
    """One attempt by a solver at a win-this-turn puzzle."""

    competitor: Competitor
    puzzle: Puzzle
    seed: int
    max_steps: int | None = None
    kind = "puzzle"

    def __post_init__(self):
        if self.competitor.deck is not None:
            raise ValueError("puzzle competitors have no deck; the puzzle supplies the cards")

    @property
    def competitors(self) -> tuple[Competitor, ...]:
        return (self.competitor,)

    def play(self, engine, index: int) -> list[GameResult]:
        with seated(self.competitors) as seats, self.puzzle.start(engine, seed=self.seed) as episode:
            result = play(episode, agent=seats[0], max_steps=self.max_steps, seed=self.seed)
            solved = episode.solved is True
            replay = episode.duel.replay()
        return [
            GameResult(
                index, 0, self.kind, self.puzzle.name, self.seed, tuple(seats[0].results),
                self.competitor.name if solved else None, None, result.reason, solved,
                result.returns, result.step_count, result.terminated, result.truncated, replay,
            )
        ]

    def describe(self) -> dict:
        return {"kind": self.kind, "competitors": [self.competitor.name], "puzzle": self.puzzle.name,
                "seed": self.seed, "max_steps": self.max_steps}

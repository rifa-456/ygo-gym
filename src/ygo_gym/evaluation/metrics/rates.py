from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

import pyarrow as pa

from ..result import GameResult
from .intervals import check_confidence, wilson
from .outcomes import contests


@dataclass(frozen=True, slots=True)
class SolveRate:
    """Share of puzzle attempts each competitor solved, with Wilson intervals."""

    confidence: float = 0.95
    name: str = "solve_rate"

    def __post_init__(self):
        check_confidence(self.confidence)

    def compute(self, results: Sequence[GameResult]) -> pa.Table:
        tallies = defaultdict(lambda: [0, 0])
        for result in results:
            if result.kind == "puzzle":
                tally = tallies[result.competitors[0]]
                tally[0] += 1
                tally[1] += bool(result.solved)
        rows = []
        for competitor, (attempts, solved) in sorted(tallies.items()):
            low, high = wilson(solved, attempts, self.confidence)
            rows.append({"competitor": competitor, "attempts": attempts, "solved": solved,
                         "rate": solved / attempts, "low": low, "high": high})
        return pa.Table.from_pylist(rows, schema=SOLVE_SCHEMA)


SOLVE_SCHEMA = pa.schema([
    ("competitor", pa.string()), ("attempts", pa.int64()), ("solved", pa.int64()),
    ("rate", pa.float64()), ("low", pa.float64()), ("high", pa.float64()),
])


@dataclass(frozen=True, slots=True)
class WinRate:
    """Cross-play matrix in long form: each competitor's score against each opponent.

    A draw, including a truncated duel, counts as half a win. unit="match"
    scores whole matches instead of duels; by_seat splits duels by the
    competitor's engine seat, where seat 0 takes the first turn.
    """

    unit: str = "game"
    by_seat: bool = False
    confidence: float = 0.95

    def __post_init__(self):
        check_confidence(self.confidence)
        if self.unit not in ("game", "match"):
            raise ValueError('unit must be "game" or "match"')
        if self.by_seat and self.unit == "match":
            raise ValueError("matches change seats between duels; by_seat needs unit='game'")

    @property
    def name(self) -> str:
        return ("win_rate" if self.unit == "game" else "match_win_rate") + ("_by_seat" if self.by_seat else "")

    def scores(self, results: Sequence[GameResult]):
        if not self.by_seat:
            for outcome in contests(results, self.unit):
                yield outcome.first, outcome.second, None, outcome.score
                yield outcome.second, outcome.first, None, 1 - outcome.score
            return
        for result in results:
            if len(result.seats) == 2:
                for seat, (competitor, opponent) in enumerate((result.competitors, result.competitors[::-1])):
                    yield competitor, opponent, seat, 0.5 if result.winner is None else float(result.winner == competitor)

    def compute(self, results: Sequence[GameResult]) -> pa.Table:
        tallies = defaultdict(lambda: [0, 0, 0])
        for competitor, opponent, seat, score in self.scores(results):
            tallies[competitor, opponent, seat][0 if score == 1 else 1 if score == 0.5 else 2] += 1
        rows = []
        for (competitor, opponent, seat), (wins, draws, losses) in sorted(tallies.items(), key=order):
            played = wins + draws + losses
            low, high = wilson(wins + draws / 2, played, self.confidence)
            rows.append({"competitor": competitor, "opponent": opponent, "seat": seat, "played": played,
                         "wins": wins, "draws": draws, "losses": losses, "rate": (wins + draws / 2) / played,
                         "low": low, "high": high})
        return pa.Table.from_pylist(rows, schema=WIN_SCHEMA)


def order(item):
    competitor, opponent, seat = item[0]
    return competitor, opponent, -1 if seat is None else seat


WIN_SCHEMA = pa.schema([
    ("competitor", pa.string()), ("opponent", pa.string()), ("seat", pa.int64()), ("played", pa.int64()),
    ("wins", pa.int64()), ("draws", pa.int64()), ("losses", pa.int64()), ("rate", pa.float64()),
    ("low", pa.float64()), ("high", pa.float64()),
])

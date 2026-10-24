import math
import random
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

import pyarrow as pa

from ..result import GameResult
from .intervals import check_confidence, percentile_interval
from .outcomes import Outcome, contests

ELO_SCALE = 400 / math.log(10)
RATING_SCHEMA = pa.schema([
    ("competitor", pa.string()), ("played", pa.int64()), ("rating", pa.float64()),
    ("low", pa.float64()), ("high", pa.float64()),
])


def bradley_terry(outcomes: Sequence[Outcome], names: Sequence[str], prior: float) -> dict[str, float]:
    """Hunter's MM fit on an Elo scale centred at 0; each competitor also scores
    prior/2 wins and losses against a fixed reference, which keeps unbeaten
    competitors finite."""
    wins = defaultdict(float)
    pairs = Counter()
    for outcome in outcomes:
        wins[outcome.first] += outcome.score
        wins[outcome.second] += 1 - outcome.score
        pairs[outcome.first, outcome.second] += 1
        pairs[outcome.second, outcome.first] += 1
    opponents = defaultdict(list)
    for (name, other), count in pairs.items():
        opponents[name].append((other, count))
    strength = dict.fromkeys(names, 1.0)
    for _ in range(10000):
        updated = {}
        for name in names:
            own = strength[name]
            denominator = prior / (own + 1.0) + sum(
                count / (own + strength[other]) for other, count in opponents[name]
            )
            updated[name] = (wins[name] + prior / 2) / denominator
        change = max(abs(math.log(updated[n] / strength[n])) for n in names)
        strength = updated
        if change < 1e-10:
            break
    ratings = {name: ELO_SCALE * math.log(value) for name, value in strength.items()}
    centre = sum(ratings.values()) / len(ratings)
    return {name: rating - centre for name, rating in ratings.items()}


def elo(outcomes: Sequence[Outcome], names: Sequence[str], k: float) -> dict[str, float]:
    ratings = dict.fromkeys(names, 0.0)
    for outcome in outcomes:
        expected = 1 / (1 + 10 ** ((ratings[outcome.second] - ratings[outcome.first]) / 400))
        delta = k * (outcome.score - expected)
        ratings[outcome.first] += delta
        ratings[outcome.second] -= delta
    return ratings


def check(unit: str, resamples: int, confidence: float) -> None:
    if unit not in ("game", "match"):
        raise ValueError('unit must be "game" or "match"')
    if type(resamples) is not int or resamples < 0:
        raise ValueError("resamples must be a nonnegative integer")
    check_confidence(confidence)


@dataclass(frozen=True, slots=True)
class RatingTable:
    """Point ratings from all contests, with intervals from bootstrap resamples of them."""

    unit: str
    resamples: int
    confidence: float
    seed: int

    def build(self, results: Sequence[GameResult], fit) -> pa.Table:
        outcomes = contests(results, self.unit)
        names = sorted({n for o in outcomes for n in (o.first, o.second)})
        if not names:
            return pa.Table.from_pylist([], schema=RATING_SCHEMA)
        point = fit(outcomes, names)
        rng = random.Random(self.seed)
        samples = defaultdict(list)
        for _ in range(self.resamples):
            drawn = sorted(rng.randrange(len(outcomes)) for _ in outcomes)
            for name, value in fit([outcomes[i] for i in drawn], names).items():
                samples[name].append(value)
        played = Counter(n for o in outcomes for n in (o.first, o.second))
        rows = []
        for name in sorted(names, key=lambda n: -point[n]):
            low, high = percentile_interval(samples[name], self.confidence) if samples else (point[name], point[name])
            rows.append({"competitor": name, "played": played[name], "rating": point[name], "low": low, "high": high})
        return pa.Table.from_pylist(rows, schema=RATING_SCHEMA)


@dataclass(frozen=True, slots=True)
class BradleyTerry:
    """Order-independent ratings on the Elo scale, with bootstrap intervals over contests."""

    unit: str = "game"
    prior: float = 1.0
    resamples: int = 200
    confidence: float = 0.95
    seed: int = 0

    def __post_init__(self):
        check(self.unit, self.resamples, self.confidence)
        if self.prior <= 0:
            raise ValueError("prior must be positive")

    @property
    def name(self) -> str:
        return "bradley_terry" if self.unit == "game" else "match_bradley_terry"

    def compute(self, results: Sequence[GameResult]) -> pa.Table:
        table = RatingTable(self.unit, self.resamples, self.confidence, self.seed)
        return table.build(results, lambda outcomes, names: bradley_terry(outcomes, names, self.prior))


@dataclass(frozen=True, slots=True)
class Elo:
    """Sequential ratings in play order, starting at 0; resamples keep that order."""

    unit: str = "game"
    k: float = 16.0
    resamples: int = 200
    confidence: float = 0.95
    seed: int = 0

    def __post_init__(self):
        check(self.unit, self.resamples, self.confidence)

    @property
    def name(self) -> str:
        return "elo" if self.unit == "game" else "match_elo"

    def compute(self, results: Sequence[GameResult]) -> pa.Table:
        table = RatingTable(self.unit, self.resamples, self.confidence, self.seed)
        return table.build(results, lambda outcomes, names: elo(outcomes, names, self.k))

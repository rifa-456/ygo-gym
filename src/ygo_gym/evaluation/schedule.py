from collections.abc import Iterable
from itertools import combinations

from ..match import MatchRules
from ..puzzle import Puzzle
from ..rules import DuelConfig
from .competitor import Competitor
from .games import DuelGame, MatchGame, PuzzleGame


def unique(competitors: Iterable[Competitor]) -> tuple[Competitor, ...]:
    values = tuple(competitors)
    if len({c.name for c in values}) != len(values):
        raise ValueError("competitor names must be unique")
    return values


def puzzles(
    competitors: Iterable[Competitor],
    selection: Iterable[Puzzle | str] | None = None,
    seeds: Iterable[int] = (0,),
    *,
    max_steps: int | None = None,
) -> tuple[PuzzleGame, ...]:
    """Every competitor attempts every puzzle once per seed; None selects every built-in puzzle."""
    names = Puzzle.list_builtin() if selection is None else selection
    chosen = tuple(p if isinstance(p, Puzzle) else Puzzle.builtin(p) for p in names)
    seeds = tuple(seeds)
    return tuple(
        PuzzleGame(competitor, puzzle, seed, max_steps)
        for competitor in unique(competitors)
        for puzzle in chosen
        for seed in seeds
    )


def round_robin(
    competitors: Iterable[Competitor],
    seeds: Iterable[int],
    *,
    swap_seats: bool = True,
    config: DuelConfig | None = None,
    max_steps: int | None = None,
) -> tuple[DuelGame, ...]:
    """Every pair of competitors once per seed, and again from swapped seats."""
    pairs = tuple(combinations(unique(competitors), 2))
    games = []
    for seed in seeds:
        for first, second in pairs:
            games.append(DuelGame((first, second), seed, config, max_steps))
            if swap_seats:
                games.append(DuelGame((second, first), seed, config, max_steps))
    return tuple(games)


def matches(
    competitors: Iterable[Competitor], seeds: Iterable[int], *, rules: MatchRules | None = None
) -> tuple[MatchGame, ...]:
    """Every pair of competitors plays one match per seed; the rules decide who goes first."""
    rules = MatchRules() if rules is None else rules
    pairs = tuple(combinations(unique(competitors), 2))
    return tuple(MatchGame((first, second), seed, rules) for seed in seeds for first, second in pairs)
